"""
ML Predictor Service
Machine Learning model to predict signal success probability
Uses Random Forest Classifier trained on historical signal data
"""

import os
import json
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
import joblib
import pytz


class MLPredictor:
    """Machine Learning predictor for signal success probability"""
    
    def __init__(self, db_manager, config):
        self.db = db_manager
        self.config = config
        self.model: Optional[RandomForestClassifier] = None
        self.feature_names = [
            "oi_change_pct",
            "lsr_change_pct", 
            "cvd_delta",
            "rs_score",
            "volatility_idx",
            "master_score",
            "trend_aligned",
            "rsi_value",
            "btc_regime_val",
            "decoupling_score"
        ]
        self.model_path = config.get("ML_MODEL_PATH", "services/ml_model.pkl")
        self.metrics_path = config.get("ML_METRICS_PATH", "services/ml_metrics.json")
        self.last_train_count = 0
        self.tz = pytz.timezone('America/Sao_Paulo')
        
        # Auto-training state
        self.is_training = False
        self.auto_train_interval = 30  # Retrain every 30 new samples (more aggressive)
        self.min_samples_for_training = 100
        
        # Try to load existing model
        self.load_model()
    
    def prepare_training_data(self) -> Tuple[np.ndarray, np.ndarray, List[Dict]]:
        """
        Prepare training data from database
        Returns: (X_features, y_labels, raw_signals)
        """
        print("[ML] Preparing training data from database...", flush=True)
        
        # Get signals with ai_features
        signals = self.db.get_signals_with_features(limit=1000)
        
        if not signals:
            print("[ML] No signals with features found", flush=True)
            return np.array([]), np.array([]), []
        
        X_list = []
        y_list = []
        valid_signals = []
        
        for sig in signals:
            features = sig.get("ai_features", {})
            status = sig.get("status")
            
            # Skip if missing features or status
            if not features or not status:
                continue
            
            # Create label: 1 for TP_HIT (success), 0 for SL_HIT (failure)
            # EXPIRED signals are excluded - they are inconclusive data
            if status == "TP_HIT":
                label = 1
            elif status == "SL_HIT":
                label = 0
            else:
                continue  # Skip ACTIVE and EXPIRED signals
            
            # Extract features in correct order
            try:
                feature_vector = [
                    features.get("oi_change_pct", 0),
                    features.get("lsr_change_pct", 0),
                    features.get("cvd_delta", 0),
                    features.get("rs_score", 0),
                    features.get("volatility_idx", 0),
                    features.get("master_score", 0),
                    features.get("trend_aligned", 0),
                    features.get("rsi_value", 50),
                    features.get("btc_regime_val", 2),  # Default 2=TRENDING
                    features.get("decoupling_score", 0.0)
                ]
                
                X_list.append(feature_vector)
                y_list.append(label)
                valid_signals.append(sig)
                
            except Exception as e:
                print(f"[ML] Error extracting features from signal: {e}", flush=True)
                continue
        
        X = np.array(X_list)
        y = np.array(y_list)
        
        print(f"[ML] Prepared {len(X)} samples (Wins: {sum(y)}, Losses: {len(y) - sum(y)}) - EXPIRED excluded", flush=True)
        
        return X, y, valid_signals
    
    def train_model(self, min_samples: int = 100) -> Dict:
        """
        Train Random Forest model on historical data
        Returns: metrics dictionary
        """
        self.is_training = True
        print("[ML] Starting model training...", flush=True)
        
        try:
            # Prepare data
            X, y, signals = self.prepare_training_data()
            
            if len(X) < min_samples:
                msg = f"Insufficient data: {len(X)}/{min_samples} samples"
                print(f"[ML] {msg}", flush=True)
                return {
                    "status": "INSUFFICIENT_DATA",
                    "message": msg,
                    "current_samples": len(X),
                    "required_samples": min_samples
                }
            
            # Split data (80/20 temporal split to avoid data leakage)
            split_idx = int(len(X) * 0.8)
            X_train, X_test = X[:split_idx], X[split_idx:]
            y_train, y_test = y[:split_idx], y[split_idx:]
            
            print(f"[ML] Training set: {len(X_train)}, Test set: {len(X_test)}", flush=True)
            
            # Train Random Forest
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                class_weight='balanced'  # Handle imbalanced data
            )
            
            self.model.fit(X_train, y_train)
            
            # Calculate metrics
            y_pred = self.model.predict(X_test)
            y_pred_proba = self.model.predict_proba(X_test)[:, 1]
            
            accuracy = accuracy_score(y_test, y_pred)
            precision = precision_score(y_test, y_pred, zero_division=0)
            recall = recall_score(y_test, y_pred, zero_division=0)
            f1 = f1_score(y_test, y_pred, zero_division=0)
            cm = confusion_matrix(y_test, y_pred)
            
            # Feature importance
            feature_importance = dict(zip(self.feature_names, self.model.feature_importances_))
            feature_importance_sorted = dict(sorted(feature_importance.items(), key=lambda x: x[1], reverse=True))
            
            metrics = {
                "status": "SUCCESS",
                "timestamp": int(time.time() * 1000),
                "timestamp_readable": datetime.now(self.tz).strftime("%Y-%m-%d %H:%M:%S"),
                "samples": {
                    "total": len(X),
                    "train": len(X_train),
                    "test": len(X_test),
                    "wins": int(sum(y)),
                    "losses": int(len(y) - sum(y))
                },
                "metrics": {
                    "accuracy": round(accuracy, 4),
                    "precision": round(precision, 4),
                    "recall": round(recall, 4),
                    "f1_score": round(f1, 4)
                },
                "confusion_matrix": {
                    "true_negative": int(cm[0][0]) if cm.shape[0] > 0 else 0,
                    "false_positive": int(cm[0][1]) if cm.shape[0] > 1 else 0,
                    "false_negative": int(cm[1][0]) if cm.shape[0] > 1 else 0,
                    "true_positive": int(cm[1][1]) if cm.shape[0] > 1 else 0
                },
                "feature_importance": {k: round(v, 4) for k, v in feature_importance_sorted.items()}
            }
            
            # Save model and metrics
            self.save_model()
            self.save_metrics(metrics)
            
            self.last_train_count = len(X)
            
            print(f"[ML] [OK] Model trained successfully - Accuracy: {accuracy:.2%}", flush=True)
            print(f"[ML] Top features: {list(feature_importance_sorted.keys())[:3]}", flush=True)
            
            return metrics
            
        finally:
            self.is_training = False
    
    def predict_probability(self, features: Dict) -> float:
        """
        Predict success probability for a signal
        Returns: probability (0.0 to 1.0)
        """
        if not self.model:
            print("[ML] No model loaded, returning default probability 0.5", flush=True)
            return 0.5
        
        try:
            # Extract features in correct order
            feature_vector = [
                features.get("oi_change_pct", 0),
                features.get("lsr_change_pct", 0),
                features.get("cvd_delta", 0),
                features.get("rs_score", 0),
                features.get("volatility_idx", 0),
                features.get("master_score", 0),
                features.get("trend_aligned", 0),
                features.get("rsi_value", 50),
                features.get("btc_regime_val", 2),  # Default 2=TRENDING
                features.get("decoupling_score", 0.0)
            ]
            
            X = np.array([feature_vector])
            probability = self.model.predict_proba(X)[0][1]  # Probability of class 1 (TP_HIT)
            
            return float(probability)
            
        except Exception as e:
            print(f"[ML] Error predicting probability: {e}", flush=True)
            return 0.5
    
    def save_model(self):
        """Save trained model to disk"""
        try:
            model_dir = os.path.dirname(self.model_path)
            if model_dir and not os.path.exists(model_dir):
                os.makedirs(model_dir)
            
            # Save with timestamp for versioning
            timestamp = datetime.now(self.tz).strftime("%Y-%m-%d_%H-%M")
            versioned_path = self.model_path.replace(".pkl", f"_{timestamp}.pkl")
            
            joblib.dump(self.model, self.model_path)
            joblib.dump(self.model, versioned_path)
            
            print(f"[ML] Model saved to {self.model_path}", flush=True)
            
            # Cleanup old models (keep last 5)
            self._cleanup_old_models()
            
        except Exception as e:
            print(f"[ML] Error saving model: {e}", flush=True)
    
    def load_model(self):
        """Load trained model from disk"""
        try:
            if os.path.exists(self.model_path):
                self.model = joblib.load(self.model_path)
                print(f"[ML] [OK] Model loaded from {self.model_path}", flush=True)
                return True
            else:
                print(f"[ML] No saved model found at {self.model_path}", flush=True)
                return False
        except Exception as e:
            print(f"[ML] Error loading model: {e}", flush=True)
            self.model = None
            return False
    
    def save_metrics(self, metrics: Dict):
        """Save model metrics to disk"""
        try:
            metrics_dir = os.path.dirname(self.metrics_path)
            if metrics_dir and not os.path.exists(metrics_dir):
                os.makedirs(metrics_dir)
            
            with open(self.metrics_path, 'w') as f:
                json.dump(metrics, f, indent=2)
            
            print(f"[ML] Metrics saved to {self.metrics_path}", flush=True)
            
        except Exception as e:
            print(f"[ML] Error saving metrics: {e}", flush=True)
    
    def get_metrics(self) -> Optional[Dict]:
        """Load model metrics from disk"""
        try:
            if os.path.exists(self.metrics_path):
                with open(self.metrics_path, 'r') as f:
                    return json.load(f)
            return None
        except Exception as e:
            print(f"[ML] Error loading metrics: {e}", flush=True)
            return None
    
    def get_status(self) -> Dict:
        """Get current ML system status"""
        metrics = self.get_metrics()
        
        # Count available labeled samples
        signals = self.db.get_signals_with_features(limit=1000)
        labeled_count = len([s for s in signals if s.get("status") in ["TP_HIT", "SL_HIT", "EXPIRED"]])
        
        # Calculate progress to next training
        samples_since_last_train = labeled_count - self.last_train_count
        samples_to_next_train = max(0, self.auto_train_interval - samples_since_last_train)
        
        return {
            "model_loaded": self.model is not None,
            "model_path": self.model_path,
            "available_samples": labeled_count,
            "last_training": metrics.get("timestamp_readable") if metrics else None,
            "last_accuracy": metrics.get("metrics", {}).get("accuracy") if metrics else None,
            "is_ready": self.model is not None and labeled_count >= self.min_samples_for_training,
            # Auto-training status
            "is_training": self.is_training,
            "auto_train_enabled": True,
            "samples_since_last_train": samples_since_last_train,
            "samples_to_next_train": samples_to_next_train,
            "auto_train_interval": self.auto_train_interval,
            "min_samples_required": self.min_samples_for_training,
            "training_progress_pct": min(100, int((samples_since_last_train / self.auto_train_interval) * 100)) if self.model else min(100, int((labeled_count / self.min_samples_for_training) * 100))
        }
    
    def should_retrain(self) -> bool:
        """Check if model should be retrained automatically"""
        # Don't trigger if already training
        if self.is_training:
            return False
            
        # Get current sample count
        signals = self.db.get_signals_with_features(limit=1000)
        current_count = len([s for s in signals if s.get("status") in ["TP_HIT", "SL_HIT", "EXPIRED"]])
        
        # First-time training: if no model and enough samples
        if not self.model:
            if current_count >= self.min_samples_for_training:
                print(f"[ML] Auto-train triggered: first training with {current_count} samples", flush=True)
                return True
            return False
        
        # Retrain if we have enough new samples since last training
        new_samples = current_count - self.last_train_count
        
        if new_samples >= self.auto_train_interval:
            print(f"[ML] Auto-retrain triggered: {new_samples} new samples since last training", flush=True)
            return True
        
        # Check if accuracy is too low (retrain to improve)
        metrics = self.get_metrics()
        if metrics:
            accuracy = metrics.get("metrics", {}).get("accuracy", 1.0)
            if accuracy < 0.55:  # More aggressive threshold
                print(f"[ML] Auto-retrain triggered: low accuracy {accuracy:.2%}", flush=True)
                return True
        
        return False
    
    def _cleanup_old_models(self):
        """Keep only the last 5 model versions"""
        try:
            model_dir = os.path.dirname(self.model_path)
            if not model_dir or not os.path.exists(model_dir):
                return
            
            # Find all versioned models
            base_name = os.path.basename(self.model_path).replace(".pkl", "")
            all_models = [
                f for f in os.listdir(model_dir)
                if f.startswith(base_name) and f.endswith(".pkl") and "_" in f
            ]
            
            # Sort by timestamp (newest first)
            all_models.sort(reverse=True)
            
            # Remove old models (keep last 5)
            for old_model in all_models[5:]:
                old_path = os.path.join(model_dir, old_model)
                os.remove(old_path)
                print(f"[ML] Removed old model: {old_model}", flush=True)
                
        except Exception as e:
            print(f"[ML] Error cleaning up old models: {e}", flush=True)
