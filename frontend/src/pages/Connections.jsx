import React, {useEffect, useState} from "react";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import {NavLink, useNavigate} from "react-router-dom";
import axios from "axios";
import {useSnackbar} from "../components/Snackbar.jsx";
import ConnectionModel from "../models/ConnectionModel.js";

export default function ConnectionsPage() {
    const navigate = useNavigate();
    const {showError} = useSnackbar();

    const [connections, setConnections] = useState([]);
    const [size, setSize] = useState(250);

    useEffect(() => {
        loadConnections();
    }, []);

    const loadConnections = async () => {
        try {
            const response = await axios.get("/api/connections");

            setSize(response.data.cup_size);

            const mappedConnections = response.data.connections.map(
                (conn) => new ConnectionModel(conn)
            );

            setConnections(mappedConnections);
        } catch (err) {
            showError("Anschlüsse konnte nicht geladen werden");
            console.error(err);
        }
    };


    const openConnection = (connection) => {
        navigate(`/connections/${connection.id}`, {
            state: {connection},
        });
    }

    const changeValue = async (ev) => {
        try {
            await axios.post("/api/connections/set-cup-size", {"cup_size": ev});
            setSize(ev);
        } catch (err) {
            showError("Bechergröße konnte nicht aktualisiert werden");
        }
    };

    return (<div className="pt-4 font-sans flex flex-col h-[100dvh]">
        <div className="flex items-center mb-2 flex-shrink-0">
            <NavLink to="/settings">
                <ArrowBackIcon
                    className="active:scale-95 transition-all duration-100"
                    sx={{fontSize: 40}}
                />
            </NavLink>
        </div>

        <div className="flex items-center justify-between mb-1">
            <div>
                <div className="text-[20px] font-bold mb-2">Bechergröße</div>
            </div>
        </div>

        <div className="flex gap-2 flex-wrap mb-6">
            {[250, 300, 350, 400, 450, 500].map((sizeOption) => (
                <button
                    key={sizeOption}
                    onClick={() => changeValue(sizeOption)}
                    className={`flex-1 py-3 rounded-full text-sm font-bold active:scale-95 transition-all
        ${size === sizeOption
                        ? "bg-[#1fe0a6] text-[#12211d]"
                        : "bg-[#1b2a28] text-[#8ca3af]"
                    }`}
                >
                    {sizeOption}
                </button>
            ))}
        </div>

        <div className="flex items-center justify-between mb-6">
            <div>
                <h1 className="text-[20px] font-bold mb-2">Anschlüsse</h1>
                <p className="text-[#8ca3af] text-sm mt-1">
                    Anschlüsse konfigurieren und testen
                </p>
            </div>
        </div>

        <div className="grid grid-cols-4 gap-4 pb-10">
            {connections.map((connection) => (<button
                key={connection.id}
                onClick={() => openConnection(connection)}
                className="bg-[#1b2a28] rounded-3xl p-5 text-left active:scale-[0.98] transition-all shadow-lg"
            >
                <div className="flex items-start justify-between">
                    <div>
                        <div className="text-xl font-bold text-[#8ca3af]">
                            Anschluss {connection.id}
                        </div>
                    </div>
                </div>

                <div className="mt-2 min-h-[52px]">
                    <div className={`font-semibold ${!connection.connected ? "text-sm text-[#8ca3af]" : "text-l"}`}>
                        {connection.liquid?.name ?? "Kein Getränk"}
                    </div>

                    <div className="text-sm text-[#8ca3af]">
                        {connection.liquid ? `${connection.liquid.fill}ml` : "Nicht verbunden"}
                    </div>
                </div>

                <div className="mt-6 bg-[#2a3d38] rounded-2xl py-2 text-center text-m font-medium">
                    Öffnen
                </div>
            </button>))}
        </div>
    </div>);
}