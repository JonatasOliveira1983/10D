/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    darkMode: "class",
    theme: {
        extend: {
            colors: {
                "primary": "#13a4ec",
                "background-light": "#f6f7f8",
                "background-dark": "#0a0f12",
                "neon-green": "#0bda57",
                "neon-red": "#fa5f38",
            },
            fontFamily: {
                "display": ["Space Grotesk", "sans-serif"],
                "mono": ["ui-monospace", "SFMono-Regular", "Menlo", "Monaco", "Consolas", "monospace"]
            },
        },
    },
    plugins: [],
}
