import React, { useEffect, useState, useCallback, useMemo, useRef } from 'react';
import axios from 'axios';
import './App.css';

// Import sound files
import correctSoundFile from './sounds/correct.mp3';
import incorrectSoundFile from './sounds/incorrect.mp3';

// Import interactive images
import correctImage from './images/correct.gif';
import incorrectImage from './images/incorrect.gif';

function App() {
  const [problem, setProblem] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [userAnswer, setUserAnswer] = useState('');
  const [isCorrect, setIsCorrect] = useState(null);
  const [resultImage, setResultImage] = useState(null);
  const [adaptiveFeedback, setAdaptiveFeedback] = useState(null);
  const [solutionLoading, setSolutionLoading] = useState(false);

  // Preload audio objects so they’re reused (avoid re-instantiation on every submit)
  const correctAudio = useMemo(() => new Audio(correctSoundFile), []);
  const incorrectAudio = useMemo(() => new Audio(incorrectSoundFile), []);

  // useRef to hold a cancellation token for axios requests.
  const cancelSourceRef = useRef(null);

  const fetchProblem = useCallback(async () => {
    setLoading(true);
    setError(null);
    // Reset state when fetching a new problem.
    setUserAnswer('');
    setIsCorrect(null);
    setResultImage(null);
    setAdaptiveFeedback(null);
    setSolutionLoading(false);

    // Cancel any previous request if it exists.
    if (cancelSourceRef.current) {
      cancelSourceRef.current.cancel();
    }
    cancelSourceRef.current = axios.CancelToken.source();

    try {
      const response = await axios.get("http://127.0.0.1:5001/", {
        cancelToken: cancelSourceRef.current.token
      });
      console.log("Received problem:", response.data);
      setProblem(response.data);
    } catch (err) {
      if (!axios.isCancel(err)) {
        console.error("Error fetching problem:", err);
        setError("Failed to load problem.");
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchProblem();
    // Cleanup: cancel any pending axios request on unmount.
    return () => {
      if (cancelSourceRef.current) {
        cancelSourceRef.current.cancel();
      }
    };
  }, [fetchProblem]);

  const handleSubmitAnswer = useCallback(async () => {
    if (problem && problem.answer_key) {
      const correct =
        userAnswer.trim().toLowerCase() === problem.answer_key.trim().toLowerCase();
      setIsCorrect(correct);

      // Play the appropriate sound using our preloaded audio objects.
      correct ? correctAudio.play() : incorrectAudio.play();

      // Set interactive image.
      setResultImage(correct ? correctImage : incorrectImage);

      // If the answer is incorrect, optionally generate adaptive follow-up feedback.
      if (!correct) {
        try {
          const response = await axios.post("http://127.0.0.1:5001/adaptive_explain", {
            problem_text: problem.problem_statement,
            student_answer: userAnswer,
            correct_answer: problem.answer_key
          });
          setAdaptiveFeedback(response.data);
        } catch (err) {
          console.error("Error fetching adaptive feedback:", err);
        }
      } else {
        setAdaptiveFeedback(null);
      }
    } else {
      setIsCorrect(false);
      incorrectAudio.play();
      setResultImage(incorrectImage);
    }
  }, [problem, userAnswer, correctAudio, incorrectAudio]);

  const handleShowSolution = useCallback(async () => {
    if (problem && problem.problem_number) {
      console.log("Show Solution clicked");
      setSolutionLoading(true);
      // Optionally clear current result message/image.
      setIsCorrect(null);
      setResultImage(null);
      try {
        // Make two API calls in parallel:
        const solutionRequest = axios.get("http://127.0.0.1:5001/solution", {
          params: {
            year: problem.year,
            contest: problem.contest,
            problem_number: problem.problem_number
          }
        });
        const followupRequest = axios.post("http://127.0.0.1:5001/adaptive_explain", {
          problem_text: problem.problem_statement,
          student_answer: "N/A", // dummy value to satisfy backend requirements
          correct_answer: problem.answer_key,
          show_solution: true  // flag can be used in backend if needed
        });

        const [solutionResponse, followupResponse] = await Promise.all([
          solutionRequest,
          followupRequest
        ]);

        // Combine the solution and follow-up question.
        const combinedData = {
          solution: solutionResponse.data.solution, // Expected from /solution endpoint.
          explanation: followupResponse.data.explanation, // Generic message, if any.
          followup: followupResponse.data.followup,
          selected_difficulty: followupResponse.data.selected_difficulty
        };
        setAdaptiveFeedback(combinedData);
      } catch (err) {
        console.error("Error fetching solution and follow-up:", err);
      } finally {
        setSolutionLoading(false);
      }
    }
  }, [problem]);

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>AMC 10 Practice</h1>
      </header>
      <div className="problem-card">
        {loading && <p className="info-message">Loading...</p>}
        {error && <p className="error-message">{error}</p>}
        {problem && (
          <>
            {/* Problem Statement */}
            <div
              className="problem-statement"
              dangerouslySetInnerHTML={{
                __html: renderProblemStatement(problem.problem_statement, problem.math_images)
              }}
            />
            {/* Screenshot Images */}
            {problem.screenshot_images && problem.screenshot_images.length > 0 && (
              <div className="screenshot-container">
                {problem.screenshot_images.map((src, idx) => (
                  <img
                    key={idx}
                    src={src}
                    alt={`Screenshot ${idx}`}
                    className="screenshot-image"
                    loading="lazy"
                  />
                ))}
              </div>
            )}
            {/* Answer Choices */}
            <div className="answer-choices">
              <h2>Answer Choices</h2>
              {problem.answer_choices &&
                problem.answer_choices.map((choice, index) => (
                  <img
                    key={index}
                    src={choice}
                    alt={`Answer Choice ${index}`}
                    className="answer-img"
                    loading="lazy"
                  />
                ))}
            </div>
            {/* Answer Input and Submit Button */}
            <div className="answer-input">
              <input
                type="text"
                value={userAnswer}
                onChange={(e) => setUserAnswer(e.target.value)}
                placeholder="Enter your answer"
              />
              <button onClick={handleSubmitAnswer} className="submit-btn answer-submit-btn">
                Submit
              </button>
            </div>
            {/* Result Message and Image (only when adaptive feedback is not present and solution isn’t loading) */}
            {isCorrect !== null && !adaptiveFeedback && !solutionLoading && (
              <>
                <p className={`result ${isCorrect ? 'correct' : 'incorrect'}`}>
                  {isCorrect ? "Correct! 🎉" : "Incorrect. Try again! ❌"}
                </p>
                {resultImage && (
                  <div className="result-image-container">
                    <img
                      src={resultImage}
                      alt={isCorrect ? "Correct" : "Incorrect"}
                      className="result-image"
                      loading="lazy"
                    />
                  </div>
                )}
              </>
            )}
            {/* Adaptive Feedback / Solution and Follow-up Question or Loading Message */}
            {solutionLoading && <p className="info-message">Loading Solution...</p>}
            {!solutionLoading && adaptiveFeedback && (
              <div className="adaptive-feedback">
                {adaptiveFeedback.solution && (
                  <>
                    <h3>Solution:</h3>
                    <p>{adaptiveFeedback.solution}</p>
                  </>
                )}
                {adaptiveFeedback.followup && (
                  <>
                    <h3>Follow-up Question ({adaptiveFeedback.selected_difficulty}):</h3>
                    <p>{adaptiveFeedback.followup}</p>
                  </>
                )}
              </div>
            )}
            {/* Button Group */}
            <div className="button-group">
              {isCorrect !== null && isCorrect === false && (
                <button onClick={handleShowSolution} className="solution-btn">
                  Show Solution
                </button>
              )}
              <button onClick={fetchProblem} className="next-btn">
                Next Problem
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

/**
 * Renders the problem statement.
 * Replaces math image placeholders with inline math images (with lazy loading)
 * and removes screenshot placeholders.
 */
const renderProblemStatement = (statement, mathImages = []) => {
  if (!statement) return "";
  for (let i = 0; i < mathImages.length; i++) {
    const placeholder = `{math_image_${i}}`;
    // Include the lazy loading attribute in the generated image tag.
    const imgTag = `<img src="${mathImages[i]}" alt="math" class="math-image" loading="lazy" />`;
    statement = statement.replace(new RegExp(placeholder, 'g'), imgTag);
  }
  // Remove any screenshot placeholders.
  statement = statement.replace(/{screenshot_image_\d+}/g, '');
  return statement;
};

export default App;
