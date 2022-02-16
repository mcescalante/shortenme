module.exports = {
  content: ["./shortenme/static/**/*.{html,js}", "./shortenme/templates/**/*.{html,js}"],
  theme: {
    extend: {},
  },
  plugins: [
    require('@tailwindcss/forms')
  ],
}
