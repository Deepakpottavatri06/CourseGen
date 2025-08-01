import { createRoot } from 'react-dom/client'
import axios from 'axios'
import './index.css'
import App from './App.jsx'

// Configure axios default base URL
axios.defaults.baseURL = 'https://ai-tutor-ym4i.onrender.com/api'
// axios.defaults.baseURL = 'http://localhost:4000/api' // Use this for local development


createRoot(document.getElementById('root')).render(
    <App />
)
