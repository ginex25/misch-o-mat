import { createContext, useContext, useState } from "react";
import { Snackbar, Alert } from "@mui/material";

const SnackbarContext = createContext();

export function SnackbarProvider({ children }) {
    const [snackbar, setSnackbar] = useState({ open: false, message: "" });

    const showError = (msg) => setSnackbar({ open: true, message: msg });
    const handleClose = () => setSnackbar({ open: false, message: "" });

    return (
        <SnackbarContext.Provider value={{ showError }}>
            {children}
            <Snackbar
                open={snackbar.open}
                autoHideDuration={3000}
                onClose={handleClose}
                anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
            >
                <Alert severity="error" onClose={handleClose} sx={{ width: "100%" }}>
                    {snackbar.message}
                </Alert>
            </Snackbar>
        </SnackbarContext.Provider>
    );
}

export const useSnackbar = () => useContext(SnackbarContext);