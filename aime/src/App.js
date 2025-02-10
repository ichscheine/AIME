import React, { useEffect, useState } from 'react';
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

  useEffect(() => {
    fetchProblem();
  }, []);

  const fetchProblem = () => {
    setLoading(true);
    setError(null);
    // Reset states when fetching a new problem.
    setUserAnswer('');
    setIsCorrect(null);
    setResultImage(null);
    setAdaptiveFeedback(null);

    axios.get("http://127.0.0.1:5001/")
      .then(response => {
        console.log("Received problem:", response.data);
        setProblem(response.data);
        setLoading(false);
      })
      .catch(error => {
        console.error("Error fetching problem:", error);
        setError("Failed to load problem.");
        setLoading(false);
      });
  };

  const handleSubmitAnswer = () => {
    if (problem && problem.answer_key) {
      const correct = userAnswer.trim().toLowerCase() === problem.answer_key.trim().toLowerCase();
      setIsCorrect(correct);
      // Play appropriate sound effect.
      const audio = new Audio(correct ? correctSoundFile : incorrectSoundFile);
      audio.play();
      // Set interactive image.
      setResultImage(correct ? correctImage : incorrectImage);
      // If incorrect, get adaptive feedback.
      if (!correct) {
        axios.post("http://127.0.0.1:5001/adaptive_explain", {
          problem_text: problem.problem_statement,
          student_answer: userAnswer,
          correct_answer: problem.answer_key,
          show_solution: false
        })
          .then(response => {
            setAdaptiveFeedback(response.data);
          })
          .catch(error => {
            console.error("Error fetching adaptive feedback:", error);
          });
      } else {
        setAdaptiveFeedback(null);
      }
    } else {
      setIsCorrect(false);
      new Audio(incorrectSoundFile).play();
      setResultImage(incorrectImage);
    }
  };

  // New function: When "Show Solution" is clicked, fetch the explanation.
  const handleShowSolution = () => {
    if (problem && problem.answer_key) {
      axios.post("http://127.0.0.1:5001/adaptive_explain", {
        problem_text: problem.problem_statement,
        student_answer: "", // We don't need a student answer here.
        correct_answer: problem.answer_key,
        show_solution: true
      })
        .then(response => {
          setAdaptiveFeedback(response.data);
        })
        .catch(error => {
          console.error("Error showing solution:", error);
        });
    }
  };

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
              dangerouslySetInnerHTML={{ __html: renderProblemStatement(problem.problem_statement, problem.math_images) }} 
            />
            {/* Screenshot Images */}
            {problem.screenshot_images && problem.screenshot_images.length > 0 && (
              <div className="screenshot-container">
                {problem.screenshot_images.map((src, idx) => (
                  <img key={idx} src={src} alt={`Screenshot ${idx}`} className="screenshot-image" />
                ))}
              </div>
            )}
            {/* Answer Choices */}
            <div className="answer-choices">
              <h2>Answer Choices</h2>
              {problem.answer_choices && problem.answer_choices.map((choice, index) => (
                <img key={index} src={choice} alt={`Answer Choice ${index}`} className="answer-img" />
              ))}
            </div>
            {/* Answer Input */}
            <div className="answer-input">
              <input
                type="text"
                value={userAnswer}
                onChange={(e) => setUserAnswer(e.target.value)}
                placeholder="Enter your answer"
              />
              <button onClick={handleSubmitAnswer}>Submit</button>
            </div>
            {/* Result Message and Image */}
            {isCorrect !== null && (
              <>
                <p className={`result ${isCorrect ? 'correct' : 'incorrect'}`}>
                  {isCorrect ? "Correct! 🎉" : "Incorrect. Try again! ❌"}
                </p>
                {resultImage && (
                  <div className="result-image-container">
                    <img src={resultImage} alt={isCorrect ? "Correct" : "Incorrect"} className="result-image" />
                  </div>
                )}
              </>
            )}
            {/* Adaptive Feedback */}
            {adaptiveFeedback && (
              <div className="adaptive-feedback">
                <h3>Explanation:</h3>
                <p>{adaptiveFeedback.explanation}</p>
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
              <button onClick={handleShowSolution} className="solution-btn">Show Solution</button>
              <button onClick={fetchProblem} className="next-btn">Next Problem</button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

/**
 * Renders the problem statement.
 * Replaces math image placeholders with inline math images and removes screenshot placeholders.
 */
const renderProblemStatement = (statement, mathImages = []) => {
  if (!statement) return "";
  for (let i = 0; i < mathImages.length; i++) {
    const placeholder = `{math_image_${i}}`;
    const imgTag = `<img src="${mathImages[i]}" alt="math" class="math-image" />`;
    statement = statement.replace(new RegExp(placeholder, 'g'), imgTag);
  }
  statement = statement.replace(/{screenshot_image_\d+}/g, '');
  return statement;
};

export default App;
