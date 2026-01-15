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
            "rsi_value"
        ]
        self.model_path = config.get("ML_MODEL_PATH", "services/ml_model.pkl")
        self.metrics_path = config.get("ML_METRICS_PATH", "services/ml_metrics.json")
        self.last_train_count = 0
        self.tz = pytz.timezone('America/Sao_Paulo')
        
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
            
            # Create label: 1 for TP_HIT (success), 0 for SL_HIT or EXPIRED (failure)
            if status == "TP_HIT":
                label = 1
            elif status in ["SL_HIT", "EXPIRED"]:
                label = 0
            else:
                continue  # Skip ACTIVE signals
            
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
                    features.get("rsi_value", 50)
                ]
                
                X_list.append(feature_vector)
                y_list.append(label)
                valid_signals.append(sig)
                
            except Exception as e:
                print(f"[ML] Error extracting features from signal: {e}", flush=True)
                continue
        
        X = np.array(X_list)
        y = np.array(y_list)
        
        print(f"[ML] Prepared {len(X)} samples (Wins: {sum(y)}, Losses: {len(y) - sum(y)})", flush=True)
        
        return X, y, valid_signals
    
    def train_model(self, min_samples: int = 100) -> Dict:
        """
        Train Random Forest model on historical data
        Returns: metrics dictionary
        """
        print("[ML] Starting model training...", flush=True)
        
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
        
        print(f"[ML] ✅ Model trained successfully - Accuracy: {accuracy:.2%}", flush=True)
        print(f"[ML] Top features: {list(feature_importance_sorted.keys())[:3]}", flush=True)
        
        return metrics
    
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
                features.get("rsi_value", 50)
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
                print(f"[ML] ✅ Model loaded from {self.model_path}", flush=True)
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
        
        # Count available samples
        signals = self.db.get_signals_with_features(limit=1000)
        labeled_count = len([s for s in signals if s.get("status") in ["TP_HIT", "SL_HIT", "EXPIRED"]])
        
        return {
            "model_loaded": self.model is not None,
            "model_path": self.model_path,
            "available_samples": labeled_count,
            "last_training": metrics.get("timestamp_readable") if metrics else None,
            "last_accuracy": metrics.get("metrics", {}).get("accuracy") if metrics else None,
            "is_ready": self.model is not None and labeled_count >= self.config.get("ML_MIN_SAMPLES", 100)
        }
    
    def should_retrain(self) -> bool:
        """Check if model should be retrained"""
        if not self.model:
            return True
        
        # Get current sample count
        signals = self.db.get_signals_with_features(limit=1000)
        current_count = len([s for s in signals if s.get("status") in ["TP_HIT", "SL_HIT", "EXPIRED"]])
        
        # Retrain if we have enough new samples
        new_samples = current_count - self.last_train_count
        retrain_interval = self.config.get("ML_AUTO_RETRAIN_INTERVAL", 50)
        
        if new_samples >= retrain_interval:
            print(f"[ML] Auto-retrain triggered: {new_samples} new samples", flush=True)
            return True
        
        # Check if accuracy is too low
        metrics = self.get_metrics()
        if metrics:
            accuracy = metrics.get("metrics", {}).get("accuracy", 1.0)
            if accuracy < 0.60:
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
