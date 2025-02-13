import React, { useEffect, useState, useCallback, useMemo, useRef } from 'react';
import axios from 'axios';
import './App.css';

// Import sound files
import correctSoundFile from './sounds/correct.mp3';
import incorrectSoundFile from './sounds/incorrect.mp3';

// Import interactive images
import correctImage from './images/correct.gif';
import incorrectImage from './images/incorrect.gif';

// Import ReactMarkdown and math plugins for rendering markdown content with LaTeX
import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';

function App() {
  const [problem, setProblem] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [userAnswer, setUserAnswer] = useState('');
  const [isCorrect, setIsCorrect] = useState(null);
  const [resultImage, setResultImage] = useState(null);

  const [solutionData, setSolutionData] = useState(null); // Holds adaptive content
  const [solutionLoading, setSolutionLoading] = useState(false);
  const [loadingProgress, setLoadingProgress] = useState(0);

  const [startTime, setStartTime] = useState(null);
  const [timeSpent, setTimeSpent] = useState(null);

  // Toggle to show/hide solution after it's loaded
  const [showSolution, setShowSolution] = useState(false);

  // Preload audio objects.
  const correctAudio = useMemo(() => new Audio(correctSoundFile), []);
  const incorrectAudio = useMemo(() => new Audio(incorrectSoundFile), []);

  // useRef for cancellation token.
  const cancelSourceRef = useRef(null);

  /**
   * Fetch a new problem from the server.
   */
  const fetchProblem = useCallback(async () => {
    setLoading(true);
    setError(null);
    setUserAnswer('');
    setIsCorrect(null);
    setResultImage(null);
    setSolutionData(null);
    setSolutionLoading(false);
    setLoadingProgress(0);
    setTimeSpent(null);
    setShowSolution(false); // Hide solution when fetching a new problem

    if (cancelSourceRef.current) {
      cancelSourceRef.current.cancel();
    }
    cancelSourceRef.current = axios.CancelToken.source();

    try {
      const response = await axios.get("http://127.0.0.1:5001/", {
        cancelToken: cancelSourceRef.current.token,
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

  /**
   * Handle answer submission.
   */
  const handleSubmitAnswer = useCallback(() => {
    // Do not update if the solution is already loaded.
    if (solutionData) return;

    if (problem && problem.answer_key) {
      const correct = userAnswer.trim().toLowerCase() === problem.answer_key.trim().toLowerCase();
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

  /**
   * Fetch solution (adaptive content) from the server.
   */
  const handleShowSolution = useCallback(async () => {
    if (!problem || !problem.problem_number || !problem.year || !problem.contest) return;

    console.log("Show Solution clicked");
    setSolutionLoading(true);
    setLoadingProgress(0);

    const progressInterval = setInterval(() => {
      setLoadingProgress(prev => (prev < 90 ? prev + 10 : prev));
    }, 200);

    try {
      const response = await axios.get("http://127.0.0.1:5001/adaptive_learning", {
        params: {
          year: problem.year,
          contest: problem.contest,
          problem_number: problem.problem_number,
          difficulty: "medium", // Adjust as needed.
        },
      });
      clearInterval(progressInterval);
      setLoadingProgress(100);
      setSolutionData(response.data);
      setShowSolution(true);
    } catch (err) {
      console.error("Error fetching adaptive learning data:", err);
    } finally {
      clearInterval(progressInterval);
      setSolutionLoading(false);
    }
  }, [problem]);

  /**
   * Render the problem statement by replacing math image placeholders with <img> tags.
   */
  const renderProblemStatement = (statement, mathImages = []) => {
    if (!statement) return "";
    let updated = statement;
    for (let i = 0; i < mathImages.length; i++) {
      const placeholder = `{math_image_${i}}`;
      const imgTag = `<img src="${mathImages[i]}" alt="math" class="math-image" loading="lazy" />`;
      updated = updated.replace(new RegExp(placeholder, 'g'), imgTag);
    }
    // Remove screenshot placeholders if any.
    updated = updated.replace(/{screenshot_image_\d+}/g, '');
    return updated;
  };

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>AMC 10 Practice</h1>
      </header>

      <main className="problem-card">
        {/* Loading and Error States */}
        {loading && <p className="info-message">Loading...</p>}
        {error && <p className="error-message">{error}</p>}

        {/* Problem Section */}
        {problem && !loading && (
          <section className="question-section">
            <h2>Problem</h2>
            <div
              className="problem-statement"
              dangerouslySetInnerHTML={{
                __html: renderProblemStatement(problem.problem_statement, problem.math_images),
              }}
            />
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
          </section>
        )}

        {/* Answer Section */}
        {problem && !loading && (
          <section className="answer-section">
            <h2>Answer Choices</h2>
            <div className="answer-choices">
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
            {timeSpent && (
              <p className="info-message" style={{ marginTop: '0.5rem' }}>
                Time Spent: {timeSpent} seconds
              </p>
            )}
            {isCorrect !== null && !solutionData && !solutionLoading && (
              <>
                <p className={`result ${isCorrect ? 'correct' : 'incorrect'}`}>
                  {isCorrect ? 'Correct! 🎉' : 'Incorrect. Try again! ❌'}
                </p>
                {resultImage && (
                  <div className="result-image-container">
                    <img
                      src={resultImage}
                      alt={isCorrect ? 'Correct' : 'Incorrect'}
                      className="result-image"
                      loading="lazy"
                    />
                  </div>
                )}
              </>
            )}
          </section>
        )}

        {/* Show Solution Button */}
        {problem && isCorrect === false && !solutionData && !solutionLoading && (
          <button onClick={handleShowSolution} className="solution-btn">
            Show Solution
          </button>
        )}

        {/* Loading progress for solution */}
        {solutionLoading && (
          <p className="info-message">
            Loading Solution: {loadingProgress}%
          </p>
        )}

        {/* Solution & Follow-up Section */}
        {solutionData && (
          <section className="solution-section">
            <div className="solution-header">
              <button
                onClick={() => setShowSolution((prev) => !prev)}
                className="toggle-solution-btn"
              >
                {showSolution ? 'Hide Solution' : 'Show Solution'}
              </button>
            </div>

            {showSolution && (
              <div className="solution-content">
                {solutionData.solution && (
                  <>
                    <h2>Solution</h2>
                    <ReactMarkdown
                      remarkPlugins={[remarkMath]}
                      rehypePlugins={[rehypeKatex]}
                    >
                      {solutionData.solution}
                    </ReactMarkdown>
                  </>
                )}

                {solutionData.followup && (
                  <>
                    <h2>Follow-up Question</h2>
                    <ReactMarkdown
                      remarkPlugins={[remarkMath]}
                      rehypePlugins={[rehypeKatex]}
                    >
                      {solutionData.followup}
                    </ReactMarkdown>
                  </>
                )}
              </div>
            )}
          </section>
        )}

        {/* Navigation Section */}
        {problem && !loading && (
          <section className="navigation-section">
            <button onClick={fetchProblem} className="next-btn">
              Next Problem
            </button>
          </section>
        )}
      </main>
    </div>
  );
}

export default App;
