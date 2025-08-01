import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Navigation from './Components/Navbar'
import HomePage from './pages/Home'
import AboutPage from './pages/About'
import RegisterPage from './pages/Register'
import LoginPage from './pages/Login'
import Dashboard from './pages/Dashboard'
import CourseDetailPage from './pages/Course'
import GenerateCoursePage from './pages/Generate'
import './App.css'

function App() {
  return (
    <Router>
      <div className="App">
        <Navigation />
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/about" element={<AboutPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/course/:id" element={<CourseDetailPage />} />
          <Route path="/generate" element={<GenerateCoursePage />} />
        </Routes>
      </div>
    </Router>
  )
}

export default App
