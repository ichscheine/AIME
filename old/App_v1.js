import React, { useState, useEffect } from "react";
import axios from "axios";

const App = () => {
    const [problems, setProblems] = useState([]);
    const [search, setSearch] = useState("");

    useEffect(() => {
        // Load problems from local JSON file or backend
        axios.get("http://localhost:5000/problems") // Change this if loading from a file
            .then(response => setProblems(response.data))
            .catch(error => console.error("Error fetching data:", error));
    }, []);

    return (
        <div style={{ padding: "20px", fontFamily: "Arial, sans-serif" }}>
            <h1>2024 AMC 10A Problems</h1>
            <input
                type="text"
                placeholder="Search problems..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                style={{ width: "100%", padding: "10px", marginBottom: "20px" }}
            />
            <div>
                {problems
                    .filter(problem => 
                        problem.problem_statement.toLowerCase().includes(search.toLowerCase())
                    )
                    .map((problem, index) => (
                        <div key={index} style={{ marginBottom: "20px", padding: "15px", border: "1px solid #ddd", borderRadius: "5px" }}>
                            <h3>Problem {index + 1}</h3>
                            <p>{problem.problem_statement}</p>
                            {problem.latex_expressions.length > 0 && (
                                <p><b>Math LaTeX:</b> {problem.latex_expressions.join(", ")}</p>
                            )}
                        </div>
                    ))}
            </div>
        </div>
    );
};

export default App;