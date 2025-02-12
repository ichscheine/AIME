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
  const [solutionData, setSolutionData] = useState(null); // Holds adaptive content from adaptive_learning collection
  const [solutionLoading, setSolutionLoading] = useState(false);
  const [loadingProgress, setLoadingProgress] = useState(0);
  const [startTime, setStartTime] = useState(null);
  const [timeSpent, setTimeSpent] = useState(null);

  // Preload audio objects.
  const correctAudio = useMemo(() => new Audio(correctSoundFile), []);
  const incorrectAudio = useMemo(() => new Audio(incorrectSoundFile), []);

  // useRef for cancellation token.
  const cancelSourceRef = useRef(null);

  const fetchProblem = useCallback(async () => {
    setLoading(true);
    setError(null);
    setUserAnswer('');
    setIsCorrect(null);
    setResultImage(null);
    setSolutionData(null); // Clear any adaptive content from previous problem.
    setSolutionLoading(false);
    setLoadingProgress(0);
    setTimeSpent(null);

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
      setStartTime(Date.now());
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
    return () => {
      if (cancelSourceRef.current) {
        cancelSourceRef.current.cancel();
      }
    };
  }, [fetchProblem]);

  const handleSubmitAnswer = useCallback(async () => {
    // Do not update if the adaptive content (solution) is already loaded.
    if (solutionData) return;

    if (problem && problem.answer_key) {
      const correct =
        userAnswer.trim().toLowerCase() === problem.answer_key.trim().toLowerCase();
      setIsCorrect(correct);
      correct ? correctAudio.play() : incorrectAudio.play();
      setResultImage(correct ? correctImage : incorrectImage);
      if (startTime) {
        const elapsed = Date.now() - startTime;
        setTimeSpent((elapsed / 1000).toFixed(1));
        console.log(`Time spent: ${elapsed / 1000} seconds`);
      }
    } else {
      setIsCorrect(false);
      incorrectAudio.play();
      setResultImage(incorrectImage);
    }
  }, [problem, userAnswer, startTime, correctAudio, incorrectAudio, solutionData]);

  const handleShowSolution = useCallback(async () => {
    if (problem && problem.problem_number && problem.year && problem.contest) {
      console.log("Show Solution clicked");
      setSolutionLoading(true);
      setLoadingProgress(0);
      setIsCorrect(null);
      setResultImage(null);

      const progressInterval = setInterval(() => {
        setLoadingProgress(prev => (prev < 90 ? prev + 10 : prev));
      }, 200);

      try {
        // Fetch adaptive learning data from our new endpoint.
        const response = await axios.get("http://127.0.0.1:5001/adaptive_learning", {
          params: {
            year: problem.year,
            contest: problem.contest,
            problem_number: problem.problem_number,
            difficulty: "medium" // Adjust difficulty as needed.
          }
        });
        clearInterval(progressInterval);
        setLoadingProgress(100);
        setSolutionData(response.data);
      } catch (err) {
        console.error("Error fetching adaptive learning data:", err);
      } finally {
        clearInterval(progressInterval);
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
            {/* Display Time Spent if available */}
            {timeSpent && <p className="info-message">Time Spent: {timeSpent} seconds</p>}
            {/* Result Message and Image (if solution is not loaded yet) */}
            {isCorrect !== null && !solutionData && !solutionLoading && (
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
            {/* Loading Progress for Adaptive Data */}
            {solutionLoading && (
              <p className="info-message">Loading Solution: {loadingProgress}%</p>
            )}
            {/* Display Adaptive Content if Loaded */}
            {solutionData && (
              <div className="adaptive-feedback">
                {solutionData.solution && (
                  <>
                    <h3>Solution:</h3>
                    <p>{solutionData.solution}</p>
                  </>
                )}
                {solutionData.followup && (
                  <>
                    <h3>Follow-up Question:</h3>
                    <p>{solutionData.followup}</p>
                  </>
                )}
              </div>
            )}
            {/* Button Group */}
            <div className="button-group">
              {isCorrect !== null && isCorrect === false && !solutionData && (
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
    const imgTag = `<img src="${mathImages[i]}" alt="math" class="math-image" loading="lazy" />`;
    statement = statement.replace(new RegExp(placeholder, 'g'), imgTag);
  }
  return statement.replace(/{screenshot_image_\d+}/g, '');
};

export default App;
