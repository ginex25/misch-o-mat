import React from 'react';
import ReactDOM from 'react-dom/client';
import {BrowserRouter} from 'react-router-dom';
import './index.css'
import App from './App';
import {SnackbarProvider} from "./components/Snackbar.jsx";

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
    <React.StrictMode>
        <BrowserRouter>
            <SnackbarProvider>
                <App/>
            </SnackbarProvider>
        </BrowserRouter>
    </React.StrictMode>
);