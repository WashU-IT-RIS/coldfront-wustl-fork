import React, {useEffect, useState} from 'react';


const PollComponent = () => {
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState('in_progress');

  useEffect(() => {
    const interval = setInterval(() => {
      fetch("/api/qumulo/progress-bar")
      .then((rest) => rest.json())
      .then((data) => {
        setProgress(data.progress);
        setStatus(data.status);
        if (data.status === 'completed') {
          clearInterval(interval);
        }
      })
      .catch((error) => console.error(error));
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div>
      <h3>Progress: {progress}%</h3>
      <p>Status: {status}</p>
    </div>
  );

};

export default PollComponent;
