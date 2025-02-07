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

    return (
        <div style={{ padding: "20px", fontFamily: "Arial, sans-serif" }}>
            <h1>2024 AMC 10A Problems</h1>

            {loading && <p>Loading problem...</p>}
            {error && <p style={{ color: "red" }}>{error}</p>}

            {problem && (
                <div style={{ marginBottom: "20px", padding: "15px", border: "1px solid #ddd", borderRadius: "5px" }}>
                    <h3>{problem.title}</h3>
                    <p>{problem.problem_statement}</p>
                    
                    {/* Display images instead of LaTeX text */}
                    {problem.image_urls.length > 0 && (
                        <div>
                            <b>Math Image:</b>
                            {problem.image_urls.map((src, index) => (
                                <img 
                                    key={index} 
                                    src={src} 
                                    alt="Math Problem" 
                                    style={{ display: "block", marginTop: "10px", maxWidth: "100%" }} 
                                />
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
