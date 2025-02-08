import React, { useState, useEffect } from "react";
import axios from "axios";

const App = () => {
    const [problem, setProblem] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const fetchProblem = () => {
        setLoading(true);
        setError(null);

        axios.get("http://localhost:5001/random_problem")
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

    useEffect(() => {
        fetchProblem();  // Fetch the first problem on page load
    }, []);

    // Function to replace {math_x} placeholders with corresponding images
    const renderProblemStatement = (statement, images) => {
        if (!statement) return null;

        return statement.split(/(\{math_\d+\})/g).map((part, index) => {
            const match = part.match(/\{math_(\d+)\}/);
            if (match) {
                const imgIndex = parseInt(match[1], 10);
                return images[imgIndex] ? (
                    <img 
                        key={index} 
                        src={images[imgIndex]} 
                        alt={`Math expression ${imgIndex}`} 
                        style={{ verticalAlign: "middle", height: "18px", margin: "0 5px" }} 
                    />
                ) : part;
            }
            return <span key={index}>{part} </span>;
        });
    };

    return (
        <div style={{ padding: "20px", fontFamily: "Arial, sans-serif" }}>
            <h1>2024 AMC 10A Problems</h1>

            {loading && <p>Loading problem...</p>}
            {error && <p style={{ color: "red" }}>{error}</p>}

            {problem && (
                <div style={{ marginBottom: "20px", padding: "15px", border: "1px solid #ddd", borderRadius: "5px" }}>
                    <h3>{problem.title}</h3>

                    {/* Render problem statement with correctly placed math images */}
                    <p>{renderProblemStatement(problem.problem_statement, problem.math_images)}</p>

                    {/* Render Screenshot Images */}
                    {problem.screenshot_images.length > 0 && (
                        <div style={{ marginTop: "15px" }}>
                            <b>Problem Diagram:</b>
                            {problem.screenshot_images.map((src, index) => (
                                <img key={index} src={src} alt="Problem Diagram" style={{ width: "100%", maxWidth: "600px", marginTop: "10px" }} />
                            ))}
                        </div>
                    )}

                    <button onClick={fetchProblem} style={{ padding: "10px", marginTop: "10px", cursor: "pointer" }}>
                        Next Problem
                    </button>
                </div>
            )}
        </div>
    );
};

export default App;
