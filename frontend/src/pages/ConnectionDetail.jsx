import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import {useLocation, useNavigate} from "react-router-dom";
import React, {useEffect, useState} from "react";
import {useSnackbar} from "../components/Snackbar.jsx";
import axios from "axios";
import {parseLiquids} from "../models/Liquid.js";

const Status = Object.freeze({
    IDLE: "idle",
    MOVING: "moving",
    STEP: "step",
    PUMPING: "pumping",
    TEST_SUCCESS: "test_success",
    TEST_FAILED: "test_failed",
    CANCELLED: "cancelled",
    FAILED: "failed",
});

export default function ConnectionDetailPage() {
    const navigate = useNavigate();
    const location = useLocation();
    const {showError} = useSnackbar();

    const {connection} = location.state;

    const [form, setForm] = useState(() => ({
        liquid: connection.liquid?.id ? String(connection.liquid.id) : null,
        fill: connection.liquid?.fill ?? 0,
        offset: connection.offset ?? 0,
    }));

    const [savedForm, setSavedForm] = useState(() => ({
        liquid: connection.liquid?.id ? String(connection.liquid.id) : null,
        fill: connection.liquid?.fill ?? 0,
        offset: connection.offset ?? 0,
    }));

    const fillOptions = React.useMemo(() => {
        const base = Array.from(
            {length: 2000 / 50 + 1},
            (_, i) => i * 50
        );

        const current = form.fill;

        if (current != null && !base.includes(current)) {
            return [...base, current].sort((a, b) => a - b);
        }

        return base;
    }, [form.fill]);

    const [isTesting, setIsTesting] = useState(false);

    const [liquids, setLiquids] = useState(() =>
        connection.liquid ? [connection.liquid] : []
    );

    const [status, setStatus] = useState(Status.IDLE);

    const statusLabels = {
        [Status.MOVING]: "Position wird angefahren...",
        [Status.STEP]: "Schritt wird ausgeführt...",
        [Status.PUMPING]: "Zapf-Test läuft...",
        [Status.TEST_SUCCESS]: "Flüssigkeit erkannt",
        [Status.TEST_FAILED]: "Keine Flüssigkeit erkannt",
        [Status.CANCELLED]: "Test abgebrochen",
        [Status.IDLE]: "Bereit",
        [Status.FAILED]: "Fehlgeschlagen",
    };

    const isBusy = status === Status.MOVING || status === Status.STEP || status === Status.PUMPING || isTesting;

    const getStatusText = () => statusLabels[status] ?? "Bereit";

    useEffect(() => {
        fetchLiquids();
    }, []);

    const fetchLiquids = async () => {
        try {
            const response = await axios.get("/api/liquids");
            const parsed = parseLiquids(response.data);
            setLiquids(parsed);
        } catch (e) {
            showError("Getränke konnten nicht geladen werden");
            console.log(e);
        }
    };

    const isDirty =
        form.liquid !== savedForm.liquid ||
        form.fill !== savedForm.fill ||
        form.offset !== savedForm.offset;

    const moveStepper = async () => {
        setStatus(Status.MOVING);

        try {
            await axios.post(`/api/calibration/move-to/${connection.id}`);
            setStatus(Status.IDLE);
        } catch (e) {
            if (e.response?.status === 400) {
                showError("Bewegung fehlgeschlagen");
                setStatus(Status.FAILED);
            } else {
                showError("Unbekannter Fehler");
                setStatus(Status.FAILED);
            }
            console.log(e);
        }
    };

    const makeStep = async (step) => {
        setStatus(Status.STEP);

        try {
            await axios.post("/api/calibration/step", {steps: step, connection: connection.id});
            setForm(prev => ({...prev, offset: prev.offset + step}));
            setStatus(Status.IDLE);
        } catch (e) {
            if (e.response?.status === 400) {
                showError("Schritt fehlgeschlagen");
            } else {
                showError("Unbekannter Fehler");
            }
            setStatus(Status.FAILED);
            console.log(e);
        }
    }

    const startTest = async () => {
        setIsTesting(true);
        setStatus(Status.PUMPING);

        try {
            const response = await axios.post(`/api/calibration/test/${connection.id}`);

            if (response.data.success) {
                setStatus(Status.TEST_SUCCESS);
            } else {
                setStatus(Status.TEST_FAILED);
                showError("Test fehlgeschlagen");
            }
        } catch (e) {
            const message = e.response?.data?.error ?? "Unbekannter Fehler";
            showError(message);
            setStatus(Status.TEST_FAILED);
            console.log(e);
        } finally {
            setIsTesting(false);
        }
    };

    const saveConfiguration = async () => {
        const originalLiquidId = connection.liquid?.id ?? null;
        const originalFill = connection.liquid?.fill ?? 0;

        const liquidChanged = form.liquid !== originalLiquidId;
        const fillChanged = form.fill !== originalFill;

        const offsetChanged = form.offset !== savedForm.offset;

        const body = {};

        if (liquidChanged) {
            body.liquid_id = form.liquid;
        }

        if (fillChanged) {
            body.liquid_fill = form.fill;
            body.liquid_id = form.liquid;
        }

        if (offsetChanged) {
            body.offset = form.offset;
        }

        if (Object.keys(body).length === 0) return;

        try {
            await axios.post(`/api/connections/${connection.id}`, body);
            setSavedForm({...form});
        } catch (e) {
            showError("Konfiguration konnte nicht gespeichert werden");
            console.log(e);
        }
    };

    return (<div className="pt-4 font-sans flex flex-col h-[100dvh]">
        <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
                <button
                    onClick={() => navigate(-1)}
                    className="active:scale-95 transition-all"
                >
                    <ArrowBackIcon sx={{fontSize: 40}}/>
                </button>

                <div>
                    <div className="text-2xl font-bold">
                        Anschluss {connection.id}
                    </div>
                </div>
            </div>
        </div>

        <div className="flex-1 overflow-y-auto pb-24">
            <div className="bg-[#1b2a28] rounded-3xl p-5 shadow-lg mt-5">
                <div className="text-m text-[#d7e3df] mb-3">
                    Getränke-Setup
                </div>

                <label className="text-sm text-[#8ca3af] mb-2 block">
                    Getränk auswählen
                </label>

                <div className="relative mb-5">
                    <select
                        value={form.liquid}
                        onChange={(e) =>
                            setForm(prev => ({
                                ...prev,
                                liquid: e.target.value || null
                            }))
                        }
                        className="w-full appearance-none bg-[#2a3d38] text-white py-3 px-4 rounded-2xl text-lg focus:outline-none"
                    >
                        <option value="0">— kein Getränk —</option>
                        {liquids.map((liquid) => (
                            <option key={liquid.id} value={liquid.id}>
                                {liquid.name}
                                {liquid.isAlcohol ? " 🍸" : ""}
                            </option>
                        ))}
                    </select>
                    <div className="pointer-events-none absolute right-4 top-1/2 -translate-y-1/2 text-[#8ca3af]">
                        ▼
                    </div>
                </div>

                <label className="text-sm text-[#8ca3af] mb-2 block">
                    Füllstand (ml)
                </label>

                <div className="relative">
                    <select
                        value={form.fill}
                        onChange={(e) =>
                            setForm(prev => ({
                                ...prev,
                                fill: Number(e.target.value)
                            }))
                        }
                        className="w-full appearance-none bg-[#2a3d38] text-white py-3 px-4 rounded-2xl text-lg focus:outline-none"
                    >
                        {fillOptions.map((value) => (<option key={value} value={value}>
                            {value} ml
                        </option>))}
                    </select>

                    <div className="pointer-events-none absolute right-4 top-1/2 -translate-y-1/2 text-[#8ca3af]">
                        ▼
                    </div>
                </div>
            </div>

            <div className="bg-[#1b2a28] rounded-3xl p-5 shadow-lg mt-5">
                <div className="text-m text-[#d7e3df] mb-3">
                    Kalibrieren
                </div>

                <div className="flex items-center justify-between bg-[#2a3d38] rounded-2xl px-4 py-3 mb-4">
                    <span className="text-m text-[#8ca3af]">Aktueller Offset</span>
                    <span className="text-white font-bold text-lg">{form.offset} Schritte</span>
                </div>

                <div className="flex gap-2 justify-between">
                    {[-15, -5, -1, 1, 5, 15].map((step) => (<button
                        key={step}
                        onClick={() => makeStep(step)}
                        disabled={isBusy}
                        className="flex-1 bg-[#2a3d38] text-white py-3 rounded-2xl text-sm font-bold active:scale-95 transition-all disabled:opacity-50">
                        {step > 0 ? `+${step}` : step}
                    </button>))}
                </div>

                <div className="flex p-5 gap-3 mb-3">
                    <button
                        onClick={() => moveStepper()}
                        disabled={isBusy}
                        className="flex-1 bg-[#1fe0a6] text-[#12211d] py-3 rounded-2xl font-bold active:scale-95 disabled:opacity-50"
                    >
                        Hin fahren
                    </button>

                    <button
                        onClick={startTest}
                        disabled={isBusy}
                        className="flex-1 bg-[#2a3d38] text-white py-3 rounded-2xl font-bold active:scale-95 disabled:opacity-50"
                    >
                        Anschluss Testen
                    </button>
                </div>

                <div className="text-m text-[#d7e3df]">
                    Status: {getStatusText()}
                </div>
            </div>
        </div>

        {isDirty && (
            <div className="fixed bottom-6 left-0 right-0 flex justify-center px-6 z-50">
                <button
                    onClick={saveConfiguration}
                    className="w-full max-w-sm bg-[#1fe0a6] text-[#12211d] px-5 py-4 rounded-3xl text-sm font-bold active:scale-95 shadow-xl transition-all"
                >
                    Speichern
                </button>
            </div>
        )}
    </div>);
}