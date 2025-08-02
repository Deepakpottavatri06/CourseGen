import { useState, useEffect } from "react"
import axios from "axios"
import { useNavigate, Link } from "react-router-dom"
import { BookOpen, Clock, BarChart2 } from "lucide-react" 

const DashboardPage = () => {
  const [courses, setCourses] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    const fetchCourses = async () => {
      try {
        // You might need to include a token in the headers if your API requires authentication
        const token = sessionStorage.getItem('token');
        const response = await axios.get("/course-content", {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        })
        setCourses(response.data)
      } catch (err) {
        console.error("Failed to fetch courses:", err)
        setError("Failed to load courses. Please try again later.")
      } finally {
        setLoading(false)
      }
    }

    fetchCourses()
  }, [])

  const handleCourseClick = (courseId) => {
    navigate(`/course/${courseId}`)
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[calc(100vh-64px)] bg-gray-50">
        <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-blue-500"></div>
        <p className="mt-4 text-xl text-gray-700">Loading your courses...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[calc(100vh-64px)] bg-gray-50 p-4">
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">
          <strong className="font-bold">Error!</strong>
          <span className="block sm:inline"> {error}</span>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero Section for Dashboard */}
      <section className="bg-gradient-to-br from-blue-600 to-indigo-700 text-white py-20 shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h1 className="text-5xl md:text-6xl font-extrabold mb-4 leading-tight">
            Your Personalized Learning Dashboard
          </h1>
          <p className="text-xl md:text-2xl text-blue-100 max-w-3xl mx-auto mb-8">
            Access and manage all the custom courses you've generated. Dive deep into new topics at your own pace.
          </p>
          {courses.length === 0 && (
            <Link
              to="/generate"
              className="bg-white text-blue-600 px-8 py-4 rounded-lg text-lg font-semibold hover:bg-gray-100 transition-colors shadow-md"
            >
              Generate Your First Course
            </Link>
          )}
        </div>
      </section>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {courses.length === 0 ? (
          <div className="text-center text-gray-600 text-lg p-8 bg-white rounded-lg shadow-md">
            <p className="mb-4">It looks like you haven't generated any courses yet.</p>
            <p>Click the button above to start creating your personalized learning journey!</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {courses.map((course) => (
              <div
                key={course._id}
                className="bg-white rounded-xl shadow-lg p-8 cursor-pointer hover:shadow-xl transition-all duration-300 border border-gray-100 flex flex-col"
                onClick={() => handleCourseClick(course._id)}
              >
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-2xl font-bold text-gray-900">{course.topic}</h2>
                  <BookOpen className="text-blue-500 h-6 w-6" />
                </div>
                <p className="text-gray-700 mb-2 flex items-center">
                  <BarChart2 className="h-4 w-4 mr-2 text-gray-500" />
                  <span className="font-medium">Difficulty:  {course.difficulty}</span>
                </p>
                <p className="text-gray-700 mb-4 flex items-center">
                  <Clock className="h-4 w-4 mr-2 text-gray-500" />
                  <span className="font-medium">Reading Time: {course.estimated_reading_time} mins</span> 
                </p>
                <div className="mt-auto flex flex-wrap gap-2">
                  {course.sub_topics &&
                    course.sub_topics.map((sub, index) => (
                      <span
                        key={index}
                        className="bg-blue-50 text-blue-700 text-xs font-medium px-3 py-1 rounded-full border border-blue-200"
                      >
                        {sub}
                      </span>
                    ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default DashboardPage
