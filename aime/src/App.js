import React, { useState, useEffect } from "react";
import axios from "axios";

const App = () => {
    const [problems, setProblems] = useState([]);
    const [search, setSearch] = useState("");

    useEffect(() => {
        axios.get("http://127.0.0.1:5000/problems")
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
                        problem.problem_html.toLowerCase().includes(search.toLowerCase())
                    )
                    .map((problem, index) => (
                        <div key={index} style={{ marginBottom: "20px", padding: "15px", border: "1px solid #ddd", borderRadius: "5px" }}>
                            <h3>Problem {index + 1}</h3>
                            <div dangerouslySetInnerHTML={{ __html: problem.problem_html }} />
                        </div>
                    ))}
            </div>
        </div>
    );
};

export default App;
