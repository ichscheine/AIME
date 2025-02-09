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

  // This state controls which interactive image (if any) is displayed.
  const [resultImage, setResultImage] = useState(null);

  useEffect(() => {
    fetchProblem();
  }, []);

  const fetchProblem = () => {
    setLoading(true);
    setError(null);
    // Reset answer state and result image when fetching a new problem.
    setUserAnswer('');
    setIsCorrect(null);
    setResultImage(null);

    axios.get("http://localhost:5001/")
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
      
      // Play sound effects based on correctness.
      const audio = new Audio(correct ? correctSoundFile : incorrectSoundFile);
      audio.play();
      
      // Set the interactive image.
      setResultImage(correct ? correctImage : incorrectImage);
    } else {
      setIsCorrect(false);
      // Play incorrect sound if no answer key is available.
      new Audio(incorrectSoundFile).play();
      setResultImage(incorrectImage);
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
            {/* Render the problem statement with math images inline */}
            <div 
              className="problem-statement" 
              dangerouslySetInnerHTML={{ __html: renderProblemStatement(problem.problem_statement, problem.math_images) }} 
            />
            {/* Render screenshot images below the statement */}
            {problem.screenshot_images && problem.screenshot_images.length > 0 && (
              <div className="screenshot-container">
                {problem.screenshot_images.map((src, idx) => (
                  <img key={idx} src={src} alt={`Screenshot ${idx}`} className="screenshot-image" />
                ))}
              </div>
            )}
            <div className="answer-choices">
              <h2>Answer Choices</h2>
              {problem.answer_choices && problem.answer_choices.map((choice, index) => (
                <img key={index} src={choice} alt={`Answer Choice ${index}`} className="answer-img" />
              ))}
            </div>
            <div className="answer-input">
              <input
                type="text"
                value={userAnswer}
                onChange={(e) => setUserAnswer(e.target.value)}
                placeholder="Enter your answer"
              />
              <button onClick={handleSubmitAnswer}>Submit</button>
            </div>
            {isCorrect !== null && (
              <>
                <p className={`result ${isCorrect ? 'correct' : 'incorrect'}`}>
                  {isCorrect ? "Correct! 🎉" : "Incorrect. Try again! ❌"}
                </p>
                {/* Display interactive result image */}
                {resultImage && (
                  <div className="result-image-container">
                    <img src={resultImage} alt={isCorrect ? "Correct" : "Incorrect"} className="result-image" />
                  </div>
                )}
              </>
            )}
            <button onClick={fetchProblem} className="next-btn">Next Problem</button>
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
  
  // Replace math image placeholders with inline image tags.
  for (let i = 0; i < mathImages.length; i++) {
    const placeholder = `{math_image_${i}}`;
    const imgTag = `<img src="${mathImages[i]}" alt="math" class="math-image" />`;
    statement = statement.replace(new RegExp(placeholder, 'g'), imgTag);
  }
  
  // Remove any screenshot image placeholders.
  statement = statement.replace(/{screenshot_image_\d+}/g, '');
  
  return statement;
};

export default App;
