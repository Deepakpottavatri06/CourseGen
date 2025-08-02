"use client"

import { useState } from "react"
import axios from "axios"
import { useNavigate } from "react-router-dom"
import { Loader2, CheckCircle, XCircle, Plus, X } from "lucide-react" // Icons for loading, success, error, add, remove

const GenerateCoursePage = () => {
  const navigate = useNavigate()
  const [formData, setFormData] = useState({
    topic: "",
    sub_topics: [], // Changed to an array
    difficulty: "beginner",
    language: "english",
  })
  const [newSubtopicInput, setNewSubtopicInput] = useState("") // State for the individual subtopic input
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState({ type: "", text: "" }) // { type: 'success' | 'error', text: '...' }

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData((prevData) => ({
      ...prevData,
      [name]: value,
    }))
  }

  const handleAddSubtopic = () => {
    const trimmedInput = newSubtopicInput.trim()
    if (trimmedInput && !formData.sub_topics.includes(trimmedInput)) {
      setFormData((prevData) => ({
        ...prevData,
        sub_topics: [...prevData.sub_topics, trimmedInput],
      }))
      setNewSubtopicInput("") // Clear the input field
    }
  }

  const handleRemoveSubtopic = (subtopicToRemove) => {
    setFormData((prevData) => ({
      ...prevData,
      sub_topics: prevData.sub_topics.filter((sub) => sub !== subtopicToRemove),
    }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setMessage({ type: "", text: "" }) // Clear previous messages

    if (formData.sub_topics.length === 0) {
      setMessage({ type: "error", text: "Please add at least one subtopic." })
      setLoading(false)
      return
    }

    try {
      const requestBody = {
        topic: formData.topic,
        sub_topics: formData.sub_topics, // Directly use the array
        difficulty: formData.difficulty,
        language: formData.language,
      }

      const token = sessionStorage.getItem("token") // Get token from session storage

      const response = await axios.post(
        "/generate-learning-content",
        requestBody,
        {
          headers: {
            Authorization: `Bearer ${token}`, 
          },
        },
      )

      if (response.status === 200 || response.status === 201 || response.status === 202) {
        setMessage({ type: "success", text: "Course generation started! You will be redirected to your dashboard shortly. Please allow a few minutes for the course to be fully prepared." })
        const newCourseId = response.data._id
        setTimeout(() => {
          navigate(`/dashboard`)
        }, 2000) // Redirect after 2 seconds
      } else {
        setMessage({ type: "error", text: response.data.message || "Failed to generate course." })
      }
    } catch (err) {
      console.error("Error generating course:", err)
      setMessage({
        type: "error",
        text: err.response?.data?.message || "Network error or server issue. Please try again.",
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-2xl w-full bg-white p-8 md:p-12 rounded-xl shadow-2xl border border-gray-100">
        <div className="text-center mb-10">
          <h2 className="text-4xl font-extrabold text-gray-900 mb-4">Generate a New Course</h2>
          <p className="text-lg text-gray-600">
            Tell us what you want to learn, and our AI will create a custom course for you.
          </p>
        </div>

        <form className="space-y-6" onSubmit={handleSubmit}>
          {message.text && (
            <div
              className={`flex items-center gap-2 p-4 rounded-lg ${
                message.type === "success"
                  ? "bg-green-100 text-green-800 border border-green-200"
                  : "bg-red-100 text-red-800 border border-red-200"
              }`}
            >
              {message.type === "success" ? <CheckCircle className="h-5 w-5" /> : <XCircle className="h-5 w-5" />}
              <p className="text-sm font-medium">{message.text}</p>
            </div>
          )}

          <div>
            <label htmlFor="topic" className="block text-sm font-medium text-gray-700 mb-2">
              Course Topic
            </label>
            <input
              id="topic"
              name="topic"
              type="text"
              required
              value={formData.topic}
              onChange={handleChange}
              className="appearance-none block w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-base"
              placeholder="e.g., Quantum Computing, Modern Web Development"
            />
          </div>

          <div>
            
            <label htmlFor="newSubtopicInput" className="block text-sm font-medium text-gray-700 mb-2">
              Subtopics
            </label>
            <div className="flex gap-2 mb-3">
              <input
                id="newSubtopicInput"
                name="newSubtopicInput"
                type="text"
                value={newSubtopicInput}
                onChange={(e) => setNewSubtopicInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault() // Prevent form submission
                    handleAddSubtopic()
                  }
                }}
                className="flex-1 px-4 py-3 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-base"
                placeholder="Add a subtopic and press Enter or click Add"
              />
              <button
                type="button"
                disabled={formData.sub_topics.length >= 8}
                onClick={handleAddSubtopic}
                className="px-4 py-3 bg-blue-600 text-white rounded-lg shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors flex items-center gap-1"
              >
                <Plus className="h-5 w-5" /> Add
              </button>
            </div>
            {formData.sub_topics.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-2">
                {formData.sub_topics.map((sub, index) => (
                  <span
                    key={index}
                    className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800 border border-blue-200"
                  >
                    {sub}
                    <button
                      type="button"
                      onClick={() => handleRemoveSubtopic(sub)}
                      className="ml-2 -mr-1 h-4 w-4 text-blue-600 hover:text-blue-800"
                      aria-label={`Remove ${sub}`}
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </span>
                ))}
              </div>
            )}
            {formData.sub_topics.length === 0 && (
              <p className="mt-2 text-sm text-red-500">Please add at least one subtopic.</p>
            )}
            {formData.sub_topics.length >= 8 && (
              <p className="mt-2 text-sm text-red-500">You can only add up to 8 subtopics.</p>
            )}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            <div>
              <label htmlFor="difficulty" className="block text-sm font-medium text-gray-700 mb-2">
                Difficulty
              </label>
              <select
                id="difficulty"
                name="difficulty"
                value={formData.difficulty}
                onChange={handleChange}
                className="block w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-base bg-white"
              >
                <option value="beginner">Beginner</option>
                <option value="intermediate">Intermediate</option>
                <option value="advanced">Advanced</option>
              </select>
            </div>

            {/* <div>
              <label htmlFor="language" className="block text-sm font-medium text-gray-700 mb-2">
                Language
              </label>
              <select
                id="language"
                name="language"
                value={formData.language}
                onChange={handleChange}
                className="block w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-base bg-white"
              >
                <option value="english">English</option>
                <option value="spanish">Spanish</option>
                <option value="french">French</option>
                <option value="german">German</option>
              </select>
            </div> */}
          </div>

          <div>
            <button
              type="submit"
              disabled={loading || formData.sub_topics.length === 0}
              className="w-full flex justify-center items-center gap-2 py-3 px-4 border border-transparent rounded-lg shadow-sm text-lg font-semibold text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-60 disabled:cursor-not-allowed transition-colors"
            >
              {loading && <Loader2 className="h-5 w-5 animate-spin" />}
              {loading ? "Generating Course..." : "Generate Course"}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default GenerateCoursePage
