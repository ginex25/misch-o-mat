import React, {useCallback, useEffect, useState} from "react";
import {Outlet} from "react-router-dom";
import axios from "axios";
import ConnectionModel from "../models/ConnectionModel.js";
import {useSnackbar} from "../components/Snackbar.jsx";

export default function ConnectionsLayout() {
    const {showError} = useSnackbar();
    const [connections, setConnections] = useState([]);
    const [size, setSize] = useState(250);
    const [loading, setLoading] = useState(true);

    const loadConnections = useCallback(async () => {
        try {
            const response = await axios.get("/api/connections");
            setSize(response.data.cup_size);
            setConnections(
                response.data.connections.map((conn) => new ConnectionModel(conn))
            );
        } catch (err) {
            showError("Anschlüsse konnte nicht geladen werden");
            console.error(err);
        } finally {
            setLoading(false);
        }
    }, [showError]);

    useEffect(() => {
        loadConnections();
    }, [loadConnections]);

    return (
        <Outlet
            context={{
                connections,
                setConnections,
                size,
                setSize,
                loading,
                loadConnections,
            }}
        />
    );
}