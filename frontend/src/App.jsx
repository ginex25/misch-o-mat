import {Routes, Route} from "react-router-dom";
import Customer from "./pages/Customer";
import Preparation from "./pages/Preparation";
import Pin from "./pages/Pin";
import Ready from "./pages/Ready";
import Settings from "./pages/Settings";
import Configuration from "./pages/Configuration";
import Calibration from "./pages/Calibration";
import Ingredients from "./pages/Ingredients";
import Cleaning from "./pages/Cleaning";
import ConnectionsPage from "./pages/Connections.jsx";
import ConnectionDetailPage from "./pages/ConnectionDetail.jsx";

function App() {
    return (
        <div className="px-4 w-full h-full">
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
                <Route path="/connections" element={<ConnectionsPage/>}/>
                <Route path="/connections/:id" element={<ConnectionDetailPage/>}/>
            </Routes>
        </div>
    );
}

export default App;
