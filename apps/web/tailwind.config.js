/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        kudryashev: ['"Kudryashev Display"', 'serif'],
        grotesk: ['"Space Grotesk"', '"PingFang SC"', '"Microsoft YaHei"', 'sans-serif'],
        helvetica: ['"Helvetica Neue Light"', '"Helvetica Neue"', 'Helvetica', 'Arial', 'sans-serif'],
      },
    },
  },
  plugins: [],
};
