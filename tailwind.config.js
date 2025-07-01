/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './marketplace/templates/**/*.html',
    './ai_assistant/templates/**/*.html',
    './static/js/**/*.js',
  ],
  theme: {
    extend: {
      colors: {
        primary: '#0056b3',
        'primary-dark': '#004494',
        'primary-light': '#1a73e8',
        'primary-lighter': '#4285f4',
        secondary: '#6c757d',
        accent: '#28a745',
        danger: '#dc3545',
        warning: '#ffc107',
        info: '#17a2b8',
      },
      fontFamily: {
        'sans': ['Inter', 'system-ui', 'sans-serif'],
      }
    }
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
  ],
}