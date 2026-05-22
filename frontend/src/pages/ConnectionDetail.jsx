import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import {useLocation, useNavigate, useOutletContext, useParams} from "react-router-dom";
import React, {useEffect, useMemo, useRef, useState} from "react";
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
    const {id: idParam} = useParams();
    const {showError} = useSnackbar();
    const {connections, loading: connectionsLoading, loadConnections} = useOutletContext();

    const connection = useMemo(() => {
        const fromState = location.state?.connection;
        if (fromState && String(fromState.id) === String(idParam)) {
            return fromState;
        }
        return connections.find((c) => String(c.id) === String(idParam));
    }, [connections, idParam, location.state?.connection]);

    const [form, setForm] = useState({
        liquid: null,
        fill: 0,
        offset: 0,
    });

    const [savedForm, setSavedForm] = useState({
        liquid: null,
        fill: 0,
        offset: 0,
    });

    const [isTesting, setIsTesting] = useState(false);

    const [liquids, setLiquids] = useState([]);

    const [status, setStatus] = useState(Status.IDLE);

    useEffect(() => {
        if (connectionsLoading || !idParam) return;
        if (!connection && connections.length > 0) {
            navigate("/connections", {replace: true});
        }
    }, [connection, connections.length, connectionsLoading, idParam, navigate]);

    useEffect(() => {
        if (!connection) return;
        const next = {
            liquid: connection.liquid?.id ? String(connection.liquid.id) : null,
            fill: connection.liquid?.fill ?? 0,
            offset: connection.offset ?? 0,
        };
        setForm(next);
        setSavedForm(next);
    }, [connection]);

    const fillOptions = React.useMemo(() => {
        const base = Array.from(
            {length: 2000 / 50 + 1},
            (_, i) => (2000 / 50 - i) * 50
        );

        const current = form.fill;

        if (current != null && !base.includes(current)) {
            return [...base, current].sort((a, b) => b - a);
        }

        return base;
    }, [form.fill]);

    const [fillOpen, setFillOpen] = useState(false);
    const fillListRef = useRef(null);

    useEffect(() => {
        if (fillOpen) {
            fillListRef.current?.scrollTo(0, 0);
        }
    }, [fillOpen]);

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

    useEffect(() => {
        if (connection?.liquid && liquids.length === 0) {
            setLiquids([connection.liquid]);
        }
    }, [connection, liquids.length]);

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
        const originalLiquidIdStr = connection.liquid?.id != null
            ? String(connection.liquid.id)
            : null;
        const originalFill = connection.liquid?.fill ?? 0;

        const liquidChanged = formLiquidStr !== originalLiquidIdStr;
        const fillChanged = form.fill !== originalFill;

        const offsetChanged = form.offset !== savedForm.offset;

        const body = {};

        if (liquidChanged) {
            body.liquid_id = String(form.liquid);
        }

        if (fillChanged) {
            body.liquid_fill = form.fill;
            body.liquid_id = formLiquidStr;
        }

        if (offsetChanged) {
            body.offset = form.offset;
        }

        if (Object.keys(body).length === 0) return;

        try {
            await axios.post(`/api/connections/${connection.id}`, body);
            setSavedForm({...form});
            await loadConnections();
        } catch (e) {
            showError("Konfiguration konnte nicht gespeichert werden");
            console.log(e);
        }
    };

    if (connectionsLoading && !connection) {
        return (
            <div className="pt-4 font-sans flex flex-col h-[100dvh] items-center justify-center text-[#8ca3af]">
                Laden…
            </div>
        );
    }

    if (!connection) {
        return null;
    }

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
                        value={form.liquid ?? "0"}
                        onChange={(e) => {
                            const v = e.target.value;
                            setForm(prev => ({
                                ...prev,
                                liquid: !v || v === "0" ? null : v,
                            }));
                        }}
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
                    <button
                        type="button"
                        onClick={() => setFillOpen((open) => !open)}
                        className="w-full text-left bg-[#2a3d38] text-white py-3 px-4 rounded-2xl text-lg focus:outline-none"
                    >
                        {form.fill} ml
                    </button>

                    {fillOpen && (
                        <>
                            <button
                                type="button"
                                aria-label="Füllstand schließen"
                                className="fixed inset-0 z-10"
                                onClick={() => setFillOpen(false)}
                            />
                            <ul
                                ref={fillListRef}
                                className="absolute z-20 mt-1 w-full max-h-60 overflow-y-auto rounded-2xl bg-[#2a3d38] shadow-lg"
                            >
                                {fillOptions.map((value) => (
                                    <li key={value}>
                                        <button
                                            type="button"
                                            onClick={() => {
                                                setForm((prev) => ({
                                                    ...prev,
                                                    fill: value,
                                                }));
                                                setFillOpen(false);
                                            }}
                                            className={`w-full px-4 py-3 text-left text-lg text-white hover:bg-[#354f48] ${
                                                value === form.fill
                                                    ? "bg-[#354f48]"
                                                    : ""
                                            }`}
                                        >
                                            {value} ml
                                        </button>
                                    </li>
                                ))}
                            </ul>
                        </>
                    )}

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