module.exports = {
  content: ["./static/**/*.{html.js}", "./templates/**/*.{html,js}"],
  theme: {
    extend: {},
  },
  plugins: [
    require('@tailwindcss/forms')
  ],
}
