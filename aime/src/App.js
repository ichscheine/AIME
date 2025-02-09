import React, { useEffect, useState } from 'react';
import axios from 'axios';

function App() {
    const [problem, setProblem] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [userAnswer, setUserAnswer] = useState(''); // State for user's answer
    const [isCorrect, setIsCorrect] = useState(null); // State to track if the answer is correct

    useEffect(() => {
        fetchProblem();
    }, []);

    const fetchProblem = () => {
        setLoading(true);
        setError(null);

        axios.get("http://localhost:5001/")
            .then(response => {
                console.log("Received problem:", response.data); // Debug JSON response
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
        if (problem && problem.correct_answer) {
            setIsCorrect(userAnswer.trim() === problem.correct_answer.trim());
        } else {
            setIsCorrect(false); // If no correct answer is available, mark as incorrect
        }
    };

    if (loading) return <p>Loading...</p>;
    if (error) return <p>{error}</p>;
    if (!problem) return <p>No problem data found.</p>;

    return (
        <div>
            <h1>{problem.title}</h1>
            <p dangerouslySetInnerHTML={{ __html: renderProblemStatement(problem.problem_statement, problem.math_images || [], problem.screenshot_images || []) }}></p>

            <h2>Answer Choices</h2>
            {problem.answer_choices && problem.answer_choices.map((choice, index) => (
                <img key={index} src={choice} alt={`Answer Choice ${index}`} style={{ maxWidth: "80%", height: "auto" }} />
            ))}

            {/* Answer Input Box */}
            <div style={{ margin: "20px 0" }}>
                <input
                    type="text"
                    value={userAnswer}
                    onChange={(e) => setUserAnswer(e.target.value)}
                    placeholder="Enter your answer"
                    style={{ padding: "10px", fontSize: "16px", width: "200px" }}
                />
                <button
                    onClick={handleSubmitAnswer}
                    style={{ padding: "10px 20px", fontSize: "16px", marginLeft: "10px" }}
                >
                    Submit
                </button>
            </div>

            {/* Display Correct/Incorrect Message */}
            {isCorrect !== null && (
                <p style={{ color: isCorrect ? "green" : "red", fontWeight: "bold" }}>
                    {isCorrect ? "Correct! 🎉" : "Incorrect. Try again! ❌"}
                </p>
            )}

            {/* Next Button */}
            <button
                onClick={fetchProblem}
                style={{ padding: "10px 20px", fontSize: "16px", marginTop: "20px" }}
            >
                Next Problem
            </button>
        </div>
    );
}

const renderProblemStatement = (statement, mathImages, screenshotImages) => {
    if (!statement) return "";

    // Replace math image placeholders with actual image tags
    for (let i = 0; i < (mathImages || []).length; i++) {
        let placeholder = `{math_image_${i}}`;
        let imgTag = `<img src="${mathImages[i]}" class="math-image" alt="math">`;
        statement = statement.replace(new RegExp(placeholder, 'g'), imgTag); // Use regex with 'g' flag for global replacement
    }

    // Replace screenshot image placeholders with actual image tags
    for (let i = 0; i < (screenshotImages || []).length; i++) {
        let placeholder = `{screenshot_image_${i}}`;
        let imgTag = `<img src="${screenshotImages[i]}" class="screenshot-image" alt="screenshot">`;
        statement = statement.replace(new RegExp(placeholder, 'g'), imgTag); // Use regex with 'g' flag for global replacement
    }

    // Remove any remaining {math_image_x} or {screenshot_image_x} placeholders
    statement = statement.replace(/{math_image_\d+}/g, ''); // Remove remaining math placeholders
    statement = statement.replace(/{screenshot_image_\d+}/g, ''); // Remove remaining screenshot placeholders

    return statement;
};

export default App;