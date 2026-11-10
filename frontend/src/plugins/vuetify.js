import 'vuetify/styles'
import { createVuetify } from 'vuetify'
import { es } from 'vuetify/locale'

export default createVuetify({
  locale: { locale: 'es', messages: { es } },
  theme: {
    defaultTheme: 'enaho',
    themes: {
      enaho: {
        dark: false,
        colors: {
          primary: '#1F4E79',
          secondary: '#2E7D32',
          error: '#C62828',
          warning: '#B26A00',
          background: '#F5F7FA',
          surface: '#FFFFFF',
        },
      },
    },
  },
  defaults: {
    VTextField: { variant: 'outlined', density: 'compact' },
    VSelect: { variant: 'outlined', density: 'compact' },
    VAutocomplete: { variant: 'outlined', density: 'compact' },
    VBtn: { variant: 'flat' },
  },
})
