import React from 'react';
import ReactDOM from 'react-dom/client';
import PollComponent from "./App";

const pollComponentDiv = document.getElementById('poll-root');

if (pollComponentDiv) {
  ReactDOM.render(<PollComponent />, pollComponentDiv);
}
