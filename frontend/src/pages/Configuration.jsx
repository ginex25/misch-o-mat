import React, {useEffect, useState} from "react";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import {NavLink} from "react-router-dom";
import axios from "axios";

function Configuration() {
    const [liquids, setLiquids] = useState([]);
    const [loading, setLoading] = useState(true);
    const [size, setSize] = useState();

    useEffect(() => {
        const fetchData = async () => {
            try {
                setLoading(true);
                const response = await axios.get(`/api/liquids`);
                setLiquids(Object.values(response.data));

                const response_2 = await axios.get(`/api/drinks/longdrinks`);
                setSize(Object.values(response_2.data)[1]);
                setTimeout(() => {
                    setLoading(false);
                }, 1000);
            } catch (err) {
                console.log(err);
                setLoading(false);
            }
        };

        fetchData();
    }, []);

    const updateData = async (val, idx, cat, file) => {
        try {
            const response = await axios.post(`/api/update/${file}`, {
                value: val,
                index: idx,
                category: cat,
            });
        } catch (err) {
            console.log(err);
        }
    };

    const changeValue = (ev, idx, cat) => {
        if (cat === 0) {
            const updatedLiquids = [...liquids];
            updatedLiquids[idx].anschlussplatz = ev;
            setLiquids(updatedLiquids);

            updateData(ev, idx + 1, "anschlussplatz", "liquid");
        } else if (cat === 1) {
            const updatedLiquids = [...liquids];
            updatedLiquids[idx].fill = ev;
            setLiquids(updatedLiquids);

            updateData(ev, idx + 1, "fuellstand_ml", "liquid");
        } else {
            setSize(ev);
            updateData(ev, idx, "gesamtmenge_ml", "longdrinks");
        }
    };

    return (
        <div className="pt-4 font-sans flex flex-col h-[100dvh]">
            <div className="flex items-center mb-2 flex-shrink-0">
                <NavLink to="/settings">
                    <ArrowBackIcon
                        className="active:scale-95 transition-all duration-100"
                        sx={{fontSize: 40}}
                    />
                </NavLink>
            </div>

            {/* Lade-Indikator wird nur für den Inhalt angezeigt */}
            {loading ? (
                <div className="flex items-center justify-center flex-grow">
                    <div className="flex space-x-[5px]">
                        <span
                            className="h-3 w-3 bg-white rounded-full opacity-0 animate-[fadeInOut_1.5s_infinite]"></span>
                        <span
                            className="h-3 w-3 bg-white rounded-full opacity-0 animate-[fadeInOut_1.5s_infinite_0.2s]"></span>
                        <span
                            className="h-3 w-3 bg-white rounded-full opacity-0 animate-[fadeInOut_1.5s_infinite_0.4s]"></span>
                    </div>
                </div>
            ) : (
                // Der Inhalt wird nur angezeigt, wenn loading false ist
                <div
                    className="overflow-y-auto flex-grow scrollbar-hide"
                    style={{scrollbarWidth: "none", msOverflowStyle: "none"}}
                >
                    <div className="flex items-center justify-between">
                        <div>
                            <div className="px-1 text-[18px] font-normal mb-4 mt-2">
                                Bechergröße
                            </div>
                            <div className="px-1 text-[13px] text-[#95c6b7] mt-[-16px] mb-4">
                                {size}ml
                            </div>
                        </div>
                        <div className="flex gap-2">
                            <select
                                value={size}
                                onChange={(ev) => changeValue(Number(ev.target.value), 0, 2)}
                                className="mr-1 text-sm rounded-full block w-[80px] p-2.5 border-r-4 border-transparent dark:bg-[#1fe0a6] dark:placeholder-[#12211d] dark:text-[#12211d] dark:focus:ring-[#1fe0a6] bg-[#1fe0a6] text-[#12211d] font-bold"
                            >
                                {[250, 300, 350, 400, 450, 500].map((sizeOption) => (
                                    <option
                                        key={sizeOption}
                                        value={sizeOption}
                                        className={`font-semibold ${
                                            size === sizeOption ? "bg-[#1fe0a6]" : ""
                                        }`}
                                    >
                                        {sizeOption}
                                    </option>
                                ))}
                            </select>
                        </div>
                    </div>
                    <div className="px-1 text-[20px] font-bold mb-2">Getränke</div>
                    <div className="px-1">
                        {liquids.map((item, index) => {
                            const assignedAnschlussplaetze = liquids.map(
                                (liquid) => liquid.anschlussplatz,
                            );
                            const options =
                                item.belegungswert === 0
                                    ? [0, ...Array.from({length: 9}, (_, i) => i + 1)].filter(
                                        (option) =>
                                            !assignedAnschlussplaetze.includes(option) ||
                                            item.anschlussplatz === option ||
                                            option === 0,
                                    )
                                    : [0, ...Array.from({length: 10}, (_, i) => i + 10)].filter(
                                        (option) =>
                                            !assignedAnschlussplaetze.includes(option) ||
                                            item.anschlussplatz === option ||
                                            option === 0,
                                    );

                            return (
                                <div
                                    key={index}
                                    className="flex flex-row items-center mb-3 justify-between"
                                >
                                    <div className="text-[18px] font-normal">
                                        {item.name}
                                        <br></br>
                                        <div className="text-[13px] text-[#95c6b7]">
                                            {item.fill}ml
                                        </div>
                                        <br></br>
                                        <div className="text-[13px] text-[#95c6b7] mt-[-28px]">
                                            Position {item.anschlussplatz}
                                        </div>
                                    </div>
                                    <div className="flex gap-6">
                                        <select
                                            className="text-sm rounded-full block w-[60px] p-2.5 border-r-4 border-transparent dark:bg-[#1fe0a6] dark:placeholder-[#12211d] dark:text-[#12211d] dark:focus:ring-[#1fe0a6] bg-[#1fe0a6] text-[#12211d] font-bold"
                                            defaultValue={item.anschlussplatz}
                                            onChange={(ev) =>
                                                changeValue(Number(ev.target.value), index, 0)
                                            }
                                        >
                                            {options.map((option) => (
                                                <option
                                                    key={option}
                                                    value={option}
                                                    className="font-semibold"
                                                >
                                                    {option === 0 ? "-" : option}
                                                </option>
                                            ))}
                                        </select>
                                        <select
                                            className="text-sm rounded-full block w-[80px] p-2.5 border-r-4 border-transparent dark:bg-[#1fe0a6] dark:placeholder-[#12211d] dark:text-[#12211d] dark:focus:ring-[#1fe0a6] bg-[#1fe0a6] text-[#12211d] font-bold"
                                            value={item.fill}
                                            onChange={(ev) =>
                                                changeValue(Number(ev.target.value), index, 1)
                                            }
                                        >
                                            {Array.from({length: 41}, (_, i) => i * 50).map(
                                                (option) => (
                                                    <option
                                                        key={option}
                                                        value={option}
                                                        className="font-semibold"
                                                    >
                                                        {option}
                                                    </option>
                                                ),
                                            )}
                                            {item.fill % 50 !== 0 && (
                                                <option
                                                    key={item.fill}
                                                    value={item.fill}
                                                    className="font-semibold"
                                                >
                                                    {item.fill}
                                                </option>
                                            )}
                                        </select>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}
        </div>
    );
}

export default Configuration;
