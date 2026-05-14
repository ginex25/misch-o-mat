import React, { useState, useEffect, useRef, useCallback } from "react";
import { Link } from "react-router-dom";
import axios from "axios";
import {useSnackbar} from "./Snackbar.jsx";

function Hero() {
  const [strength, setStrength] = useState("mittel");
  const [category, setCategory] = useState("Mischgetränke");
  const [drink, setDrink] = useState("");
  const [drinks, setDrinks] = useState([]);
  const [random, setRandom] = useState(false);
  const [loading, setLoading] = useState(true);
  const drinksCache = useRef({
    Mischgetränke: [],
    Longdrinks: [],
  });

  const scrollDivRef = useRef(null);
  const { showError } = useSnackbar();

  const toggleRandom = useCallback(() => {
    setRandom((prevRandom) => !prevRandom);
  }, []);

  const changeCategory = (category) => {
    setCategory(category);
    setDrink("");

    if (scrollDivRef.current) {
      scrollDivRef.current.scrollTo(0, 0);
    }
  };

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        if (drinksCache.current["Mischgetränke"].length === 0) {
          const response = await axios.get(`/api/drinks/mixdrinks`);
          drinksCache.current["Mischgetränke"] = Object.values(
            response.data[0],
          );
        }

        if (drinksCache.current["Longdrinks"].length === 0) {
          const response_2 = await axios.get(`/api/drinks/longdrinks`);
          drinksCache.current["Longdrinks"] = Object.values(response_2.data[0]);
        }
        setDrinks(drinksCache.current[category]);
        setTimeout(() => {
          changeCategory("Longdrinks");
          setTimeout(() => {
            changeCategory("Mischgetränke");
            setLoading(false);
          }, 1000);
        }, 1000);
      } catch (err) {
        showError("Getränke konnten nicht geladen werden");
        console.error(err);
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  useEffect(() => {
    setDrinks(drinksCache.current[category]);
  }, [category]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[365px]">
        <div className="flex space-x-[5px]">
          <span className="h-3 w-3 bg-white rounded-full opacity-0 animate-[fadeInOut_1.5s_infinite]"></span>
          <span className="h-3 w-3 bg-white rounded-full opacity-0 animate-[fadeInOut_1.5s_infinite_0.2s]"></span>
          <span className="h-3 w-3 bg-white rounded-full opacity-0 animate-[fadeInOut_1.5s_infinite_0.4s]"></span>
        </div>
      </div>
    );
  }

  return (
    <div className="font-sans">
      <div className="w-full grid grid-cols-2 text-center border-b border-[#366356]">
        <div
          className={`font-sans font-semibold text-sm border-b-[3px] ${
            category === "Mischgetränke"
              ? "border-b-[#1fe0a6]"
              : "border-b-transparent"
          } py-3`}
          onClick={() => changeCategory("Mischgetränke")}
        >
          Mischgetränke
        </div>
        <div
          className={`font-sans font-semibold text-sm border-b-[3px] ${
            category === "Longdrinks"
              ? "border-b-[#1fe0a6]"
              : "border-b-transparent"
          } py-3`}
          onClick={() => changeCategory("Longdrinks")}
        >
          Longdrinks
        </div>
      </div>

      <div
        className="overflow-x-auto whitespace-nowrap p-4 pt-6 scrollbar-hide"
        style={{ scrollbarWidth: "none", msOverflowStyle: "none" }}
        ref={scrollDivRef}
      >
        <div className="inline-flex gap-3">
          {drinks.map((item, index) => (
            <div
              key={index}
              className="flex flex-col gap-3 text-center pb-3 active:scale-95 transition-all duration-100"
              onClick={() => setDrink(item.name)}
            >
              <div className="px-4">
                <div
                  className={`w-[143px] h-[143px] bg-center bg-no-repeat aspect-square bg-cover rounded-full ${
                    drink === item.name
                      ? "border-[3px] border-[#1fe0a6] box-border"
                      : "border-0"
                  }`}
                  style={{ backgroundImage: `url(${item.url})` }}
                ></div>
              </div>
              <p className="text-white text-base font-medium leading-normal">
                {item.name}
              </p>
            </div>
          ))}
        </div>
      </div>

      <div className="w-full grid grid-cols-2 mt-2">
        <div>
          <h3
            className={`text-white text-lg font-bold leading-tight tracking-[-0.015em] px-2 pb-2 pt-4 ${
              category === "Longdrinks" ? "opacity-40" : ""
            }`}
          >
            Wähle deine Stärke
          </h3>
          <div className="flex gap-3 p-2 flex-wrap pr-4">
            <div
              className={`flex h-10 shrink-0 items-center justify-center gap-x-2 rounded-full ${
                strength === "schwach" && category !== "Longdrinks"
                  ? "bg-[#1fe0a6] text-[#12211d]"
                  : "bg-[#25463c]"
              } pl-4 pr-4 active:scale-95 transition-all duration-100 ${
                category === "Longdrinks"
                  ? "opacity-50 pointer-events-none"
                  : ""
              }`}
              onClick={() =>
                category !== "Longdrinks" && setStrength("schwach")
              }
            >
              <p
                className={`text-sm ${
                  strength === "schwach" && category !== "Longdrinks"
                    ? "font-bold"
                    : "font-medium"
                } leading-normal`}
              >
                Schwach
              </p>
            </div>
            <div
              className={`flex h-10 shrink-0 items-center justify-center gap-x-2 rounded-full ${
                strength === "mittel" && category !== "Longdrinks"
                  ? "bg-[#1fe0a6] text-[#12211d]"
                  : "bg-[#25463c]"
              } pl-4 pr-4 active:scale-95 transition-all duration-100 ${
                category === "Longdrinks"
                  ? "opacity-50 pointer-events-none"
                  : ""
              }`}
              onClick={() => category !== "Longdrinks" && setStrength("mittel")}
            >
              <p
                className={`text-sm ${
                  strength === "mittel" && category !== "Longdrinks"
                    ? "font-bold"
                    : "font-medium"
                } leading-normal`}
              >
                Mittel
              </p>
            </div>
            <div
              className={`flex h-10 shrink-0 items-center justify-center gap-x-2 rounded-full ${
                strength === "stark" && category !== "Longdrinks"
                  ? "bg-[#1fe0a6] text-[#12211d]"
                  : "bg-[#25463c]"
              } pl-4 pr-4 active:scale-95 transition-all duration-100 ${
                category === "Longdrinks"
                  ? "opacity-50 pointer-events-none"
                  : ""
              }`}
              onClick={() => category !== "Longdrinks" && setStrength("stark")}
            >
              <p
                className={`text-sm ${
                  strength === "stark" && category !== "Longdrinks"
                    ? "font-bold"
                    : "font-medium"
                } leading-normal`}
              >
                Stark
              </p>
            </div>
          </div>
        </div>
        <div className="py-1 mt-auto ml-auto mb-[4px] mr-2">
          <div className="flex flex-row items-end justify-end">
            <div className="flex mb-[-8px]">
              <label className="inline-flex items-center mb-5 cursor-pointer mr-2 ml-auto">
                <input
                  type="checkbox"
                  className="sr-only peer"
                  checked={random}
                  onChange={() => toggleRandom()}
                />
                <div className="relative w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer dark:bg-gray-800 peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full  after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[#1fe0a6]"></div>
              </label>
              <p className="mr-2">Zufällig</p>
            </div>
          </div>
          <Link
            to={"/preparation"}
            state={{
              drink,
              drinks,
              category,
              random,
              strength,
              route: "ingredients",
            }}
          >
            <button
              className={`w-[300px] h-[42px] cursor-pointer items-center justify-center rounded-full flex-1 transition-all duration-75 bg-[#1fe0a6] text-[#12211d] text-base font-bold leading-normal tracking-[0.015em] 
                                ${drink === "" && !random ? "opacity-50" : ""}`}
              disabled={drink === "" && !random}
            >
              <span className="truncate">Weiter</span>
            </button>
          </Link>
        </div>
      </div>
    </div>
  );
}

export default Hero;
