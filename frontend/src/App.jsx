import {useEffect, useRef} from "react";
import {Routes, Route, useLocation} from "react-router-dom";
import axios from "axios";
import Customer from "./pages/Customer";
import Preparation from "./pages/Preparation";
import Pin from "./pages/Pin";
import Ready from "./pages/Ready";
import Settings from "./pages/Settings";
import Configuration from "./pages/Configuration";
import Calibration from "./pages/Calibration";
import Ingredients from "./pages/Ingredients";
import Cleaning from "./pages/Cleaning";
import ConnectionsLayout from "./pages/ConnectionsLayout.jsx";
import ConnectionsPage from "./pages/Connections.jsx";
import ConnectionDetailPage from "./pages/ConnectionDetail.jsx";

function isConnectionsListPath(pathname) {
    return pathname === "/connections" || pathname === "/connections/";
}

function isConnectionsDetailPath(pathname) {
    return /^\/connections\/[^/]+\/?$/.test(pathname);
}

function ConnectionsListExitCalibrationReset() {
    const location = useLocation();
    const prevPathRef = useRef(location.pathname);

    useEffect(() => {
        const prev = prevPathRef.current;
        const next = location.pathname;
        prevPathRef.current = next;

        if (prev === next) return;
        if (!isConnectionsListPath(prev)) return;
        if (isConnectionsDetailPath(next)) return;
        if (isConnectionsListPath(next)) return;

        axios.post("/api/calibration/reset").catch((err) => {
            console.error(err);
        });
    }, [location.pathname]);

    return null;
}

function App() {
    return (
        <div className="px-4 w-full h-full">
            <ConnectionsListExitCalibrationReset/>
            <Routes>
                <Route path="/" element={<Customer/>}/>
                <Route path="/preparation" element={<Preparation/>}/>
                <Route path="/pin" element={<Pin/>}/>
                <Route path="/ready" element={<Ready/>}/>
                <Route path="/settings" element={<Settings/>}/>
                <Route path="/configuration" element={<Configuration/>}/>
                <Route path="/calibration" element={<Calibration/>}/>
                <Route path="/ingredients" element={<Ingredients/>}/>
                <Route path="/clean" element={<Cleaning/>}/>
                <Route path="/connections" element={<ConnectionsLayout/>}>
                    <Route index element={<ConnectionsPage/>}/>
                    <Route path=":id" element={<ConnectionDetailPage/>}/>
                </Route>
            </Routes>
        </div>
    );
}

export default App;