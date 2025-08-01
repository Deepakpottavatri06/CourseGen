"use client"

import { useState, useEffect, useRef } from "react"
import { useParams, useNavigate } from "react-router-dom"
import axios from "axios"
import { ArrowLeft, CheckCircle2, Bookmark, Loader2 } from "lucide-react" // Importing icons, added Loader2
import ReactMarkdown from 'react-markdown';
const CourseDetailPage = () => {
  const { id } = useParams()
  const navigate = useNavigate()
  const [course, setCourse] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  // State for the current page index in the unified paginated content
  const [currentPageIndex, setCurrentPageIndex] = useState(0)
  // State for marking sections as read (client-side persistence for display)
  const [readSections, setReadSections] = useState({})
  // State for active section in sidebar, derived from currentPageIndex
  const [activeSectionId, setActiveSectionId] = useState("")
  // New state to indicate if content is still generating
  const [isContentGenerating, setIsContentGenerating] = useState(false)

  // Ref for the main content area to scroll to when navigating
  const contentContainerRef = useRef(null)

  // Function to construct the unified paginated content array
  const getPaginatedContent = (courseData) => {
    if (!courseData) return []

    const content = []

    // Add Introduction
    content.push({
      id: "introduction", // Hardcoded ID for main section
      title: "Introduction",
      type: "main",
      content: {
        introduction: courseData.introduction.introduction,
        overview: courseData.introduction.overview,
      },
    })

    // Add Learning Objectives
    content.push({
      id: "learning-objectives", // Hardcoded ID for main section
      title: "Learning Objectives",
      type: "main",
      content: courseData.introduction.learning_objectives,
    })

    // Add Prerequisites
    content.push({
      id: "prerequisites", // Hardcoded ID for main section
      title: "Prerequisites",
      type: "main",
      content: courseData.introduction.prerequisites,
    })

    // Add Subtopic Contents
    courseData.subtopic_contents.forEach((subContent) => {
      content.push({
        // Prefix subtopic IDs to ensure uniqueness and avoid clashes with main sections
        id: `subtopic-${subContent.subtopic.replace(/\s+/g, "-").toLowerCase()}`,
        title: subContent.subtopic,
        type: "subtopic",
        content: subContent.content,
        sources: subContent.sources,
        read: subContent.read || false, // Include read status
      })
    })

    return content
  }

  const [paginatedContent, setPaginatedContent] = useState([])

  useEffect(() => {
    const fetchCourseDetails = async () => {
      try {
        const token = sessionStorage.getItem("token") // Get token from session storage
        const response = await axios.get(`/course-content/${id}`, {
          headers: {
            Authorization: `Bearer ${token}`, // Include the token in the header
          },
        })
        const foundCourse = response.data

        if (foundCourse) {
          // Check if content_loaded is false
          if (!foundCourse.content_loaded) {
            setIsContentGenerating(true)
            setLoading(false) // Stop main loading, but show generating message
            return // Exit early, don't process content yet
          }

          setCourse(foundCourse)
          const fullContent = getPaginatedContent(foundCourse)
          setPaginatedContent(fullContent)

          // Initialize read status for all subtopic sections
          const initialReadStatus = {}
          fullContent.forEach((section) => {
            if (section.type === "subtopic") {
              initialReadStatus[section.id] = false
            }
          })
          setReadSections(initialReadStatus)

          // Set initial active section
          if (fullContent.length > 0) {
            setActiveSectionId(fullContent[0].id)
          }
        } else {
          setError("Course not found.")
        }
      } catch (err) {
        console.error("Failed to fetch course details:", err)
        setError("Failed to load course details. Please try again later.")
      } finally {
        setLoading(false)
      }
    }

    fetchCourseDetails()
  }, [id])

  // Update activeSectionId when currentPageIndex changes
  useEffect(() => {
    if (paginatedContent.length > 0 && currentPageIndex >= 0 && currentPageIndex < paginatedContent.length) {
      setActiveSectionId(paginatedContent[currentPageIndex].id)
      // Scroll to the top of the content area when page changes
      contentContainerRef.current?.scrollIntoView({ behavior: "smooth", block: "start" })
    }
  }, [currentPageIndex, paginatedContent])

  const goToPage = (index) => {
    if (index >= 0 && index < paginatedContent.length) {
      setCurrentPageIndex(index)
    }
  }

  const goToPreviousPage = () => {
    goToPage(currentPageIndex - 1)
  }

  const goToNextPage = () => {
    goToPage(currentPageIndex + 1)
  }

  const handleMarkAsRead = async () => {
    const currentSection = paginatedContent[currentPageIndex]
    if (!currentSection || currentSection.type !== "subtopic") return // Only proceed if it's a subtopic

    const sectionId = currentSection.id // This is the prefixed ID
    const sectionTitle = currentSection.title // This is the original subtopic title for the API

    try {
      const token = sessionStorage.getItem("token")
      const response = await axios.put(
        `/course-content/${course._id}/read`,
        { sub_topic: sectionTitle }, // API expects sub_topic name
        {
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        },
      )
      if (response.status === 200) {
        setReadSections((prev) => ({ ...prev, [sectionId]: true }))
        console.log(`Subtopic "${sectionTitle}" marked as read via API.`)
        // Optional: Trigger a success notification
      } else {
        console.error(`Failed to mark "${sectionTitle}" as read:`, response.statusText)
        // Optional: Trigger an error notification
      }
    } catch (error) {
      console.error("Error marking subtopic as read:", error)
      // Optional: Trigger an error notification
    }
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[calc(100vh-64px)] bg-gray-50">
        <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-blue-500"></div>
        <p className="mt-4 text-xl text-gray-700">Loading course details...</p>
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
        <button
          onClick={() => navigate("/dashboard")}
          className="mt-6 bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-semibold transition-colors flex items-center"
        >
          <ArrowLeft className="h-5 w-5 mr-2" /> Back to Dashboard
        </button>
      </div>
    )
  }

  // New conditional rendering for content still generating
  if (isContentGenerating) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[calc(100vh-64px)] bg-gray-50 p-4 text-center">
        <Loader2 className="h-16 w-16 text-blue-500 animate-spin mb-4" />
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Course Content is Still Being Generated</h2>
        <p className="text-lg text-gray-700 mb-6">
          Please wait a few moments. Our AI is working hard to prepare your personalized course.
        </p>
        <button
          onClick={() => navigate("/dashboard")}
          className="mt-6 bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-semibold transition-colors flex items-center"
        >
          <ArrowLeft className="h-5 w-5 mr-2" /> Back to Dashboard
        </button>
      </div>
    )
  }

  if (!course || paginatedContent.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[calc(100vh-64px)] bg-gray-50 p-4">
        <div className="text-xl text-gray-600">Course not found or no content available.</div>
        <button
          onClick={() => navigate("/dashboard")}
          className="mt-6 bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-semibold transition-colors flex items-center"
        >
          <ArrowLeft className="h-5 w-5 mr-2" /> Back to Dashboard
        </button>
      </div>
    )
  }

  const currentContent = paginatedContent[currentPageIndex]
  const totalPages = paginatedContent.length
  const hasPreviousPage = currentPageIndex > 0
  const hasNextPage = currentPageIndex < totalPages - 1

  return (
    <div className="min-h-screen bg-gray-50 pt-20 pb-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 bg-white shadow-2xl rounded-2xl my-8 p-8 md:p-12">
        <button
          onClick={() => navigate("/dashboard")}
          className="mb-8 bg-gray-200 hover:bg-gray-300 text-gray-800 px-4 py-2 rounded-lg font-medium transition-colors flex items-center"
        >
          <ArrowLeft className="h-4 w-4 mr-2" /> Back to Dashboard
        </button>

        <div className="text-center pb-8 border-b border-gray-200 mb-10">
          <h1 className="text-4xl md:text-5xl font-extrabold text-gray-900 mb-3 leading-tight">{course.topic}</h1>
          <p className="text-lg text-gray-600">
            <span className="font-semibold">Difficulty:</span>{" "}
            {course.difficulty.charAt(0).toUpperCase() + course.difficulty.slice(1)} |
            <span className="font-semibold ml-2">Estimated Reading Time:</span> {course.estimated_reading_time} mins
          </p>
          <div className="mt-4 flex flex-wrap justify-center gap-2">
            {course.sub_topics &&
              course.sub_topics.map((sub, index) => (
                <span
                  key={index}
                  className="bg-blue-50 text-blue-700 text-sm font-medium px-3 py-1 rounded-full border border-blue-200"
                >
                  {sub}
                </span>
              ))}
          </div>
        </div>

        {/* Main content area with sidebar */}
        <div className="grid grid-cols-1 lg:grid-cols-[280px_1fr] gap-10">
          {/* Sticky Sidebar Navigation */}
          <aside className="hidden lg:block sticky top-24 h-[calc(100vh-120px)] overflow-y-auto pr-4">
            <nav className="space-y-2">
              <h3 className="text-lg font-bold text-gray-900 mb-3">Course Outline</h3>
              <ul className="space-y-1">
                {paginatedContent.map((section, index) => (
                  <li key={section.id}>
                    <button
                      onClick={() => goToPage(index)}
                      className={`w-full text-left p-2 rounded-md transition-colors flex items-center justify-between ${
                        activeSectionId === section.id
                          ? "bg-blue-100 text-blue-700 font-semibold"
                          : "text-gray-700 hover:bg-gray-100"
                      }`}
                    >
                      <span>{section.title}</span>
                      {section.type === "subtopic" && readSections[section.id] && (
                        <CheckCircle2 className="h-4 w-4 text-green-500" />
                      )}
                    </button>
                  </li>
                ))}
              </ul>
            </nav>
          </aside>

          {/* Course Content Display */}
          <div ref={contentContainerRef} className="lg:col-span-1 space-y-10">
            {currentContent && (
              <div
                key={currentContent.id} // Key to force re-render when content changes
                className={`p-8 rounded-xl shadow-md border ${
                  currentContent.type === "main"
                    ? currentContent.id === "introduction"
                      ? "bg-blue-50 border-blue-100"
                      : currentContent.id === "learning-objectives"
                        ? "bg-green-50 border-green-100"
                        : "bg-yellow-50 border-yellow-100"
                    : "bg-white border-gray-200"
                }`}
              >
                <div className="flex justify-between items-center mb-4">
                  <h2
                    className={`text-3xl font-bold ${
                      currentContent.type === "main"
                        ? currentContent.id === "introduction"
                          ? "text-blue-800"
                          : currentContent.id === "learning-objectives"
                            ? "text-green-800"
                            : "text-yellow-800"
                        : "text-blue-700"
                    }`}
                  >
                    {currentContent.title}
                  </h2>
                  {currentContent.type === "subtopic" && (
                    <button
                      onClick={handleMarkAsRead}
                      disabled={currentContent.read}
                      className={`px-4 py-2 rounded-lg font-medium transition-colors flex items-center ${
                        currentContent.read
                          ? "bg-green-100 text-green-700 cursor-not-allowed"
                          : "bg-blue-600 hover:bg-blue-700 text-white"
                      }`}
                      
                    >
                      {(currentContent.read) ? (
                        console.log("Section already marked as read"),
                        <>
                          <CheckCircle2 className="h-4 w-4 mr-2" /> Read
                        </>
                      ) : (
                        console.log("Section not marked as read",currentContent),
                        <>
                          <Bookmark className="h-4 w-4 mr-2" /> Mark as Read
                        </>
                      )}
                    </button>
                  )}
                </div>

                {currentContent.type === "main" && currentContent.id === "introduction" && (
                  <>
                    <pre className="text-gray-800 leading-relaxed whitespace-pre-wrap font-sans">
                      <ReactMarkdown>{currentContent.content.introduction}</ReactMarkdown>
                    </pre>
                    <h3 className="text-2xl font-semibold text-blue-700 mt-6 mb-3">Overview</h3>
                    <pre className="text-gray-800 leading-relaxed whitespace-pre-wrap font-sans">
                      <ReactMarkdown>{currentContent.content.overview}</ReactMarkdown>
                    </pre>
                  </>
                )}

                {currentContent.type === "main" &&
                  (currentContent.id === "learning-objectives" || currentContent.id === "prerequisites") && (
                    <ul className="list-disc list-inside text-gray-800 space-y-2">
                      {currentContent.content.map((item, index) => (
                        <li key={index}><ReactMarkdown>{item}</ReactMarkdown></li>
                      ))}
                    </ul>
                  )}

                {currentContent.type === "subtopic" && (
                  <>
                    <div
                      className="prose max-w-none text-gray-800 leading-relaxed whitespace-pre-line"
                    >
                      <ReactMarkdown>{currentContent.content}</ReactMarkdown>
                    </div>
                    {currentContent.sources && currentContent.sources.length > 0 && (
                      <div className="mt-6 text-sm text-gray-600 border-t border-gray-100 pt-4">
                        <span className="font-semibold text-gray-700">Sources:</span>
                        <ul className="list-disc list-inside mt-2 space-y-1">
                          {currentContent.sources.map((source, srcIndex) => (
                            <li key={srcIndex}>
                              <a
                                href={source}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-blue-600 hover:underline"
                              >
                                <ReactMarkdown>{source}</ReactMarkdown>
                              </a>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </>
                )}
              </div>
            )}

            {/* Pagination Controls */}
            <div className="flex justify-between items-center mt-8">
              <button
                onClick={goToPreviousPage}
                disabled={!hasPreviousPage}
                className="px-6 py-3 rounded-lg font-semibold transition-colors flex items-center gap-2
                               bg-blue-600 text-white hover:bg-blue-700 disabled:bg-gray-300 disabled:text-gray-600 disabled:cursor-not-allowed"
              >
                <ArrowLeft className="h-5 w-5" /> Previous
              </button>
              <span className="text-gray-700 font-medium">
                {currentPageIndex + 1} / {totalPages}
              </span>
              <button
                onClick={goToNextPage}
                disabled={!hasNextPage}
                className="px-6 py-3 rounded-lg font-semibold transition-colors flex items-center gap-2
                               bg-blue-600 text-white hover:bg-blue-700 disabled:bg-gray-300 disabled:text-gray-600 disabled:cursor-not-allowed"
              >
                Next <ArrowLeft className="h-5 w-5 rotate-180" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default CourseDetailPage
