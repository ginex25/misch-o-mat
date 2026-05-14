import React, { useState } from "react";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import { NavLink } from "react-router-dom";
import axios from "axios";

function Cleaning() {
  const [clicked, setClicked] = useState(false);
  const [success, setSuccess] = useState(null); // Initialize as null to handle both success and failure states
  const arrowStyle = { fontSize: 40 };

  const handleAction = async (position) => {
    setClicked(true);
    setSuccess(null);
    try {
      const response = await axios.post(`/api/clean`, {
        position: position,
      });
      setClicked(false);
      setSuccess(true); // Set success to true
    } catch (err) {
      console.log(err);
      setClicked(false);
      setSuccess(false); // Set success to false
    }
  };

  return (
    <div className="pt-4 font-sans">
      <div>
        <NavLink
          to="/settings"
          className={clicked ? "pointer-events-none opacity-50" : ""}
        >
          <ArrowBackIcon
            className="active:scale-95 transition-all duration-100"
            sx={arrowStyle}
          />
        </NavLink>
      </div>
      <div className="flex flex-col items-center">
        <div className="grid grid-cols-4 gap-4 mt-1">
          {Array.from({ length: 19 }, (_, i) => (
            <button
              key={i + 1}
              className={`${
                clicked
                  ? "bg-[#25463c] opacity-50 pointer-events-none"
                  : "bg-[#1fe0a6]"
              } w-[95px] h-[60px] cursor-pointer items-center justify-center rounded-full transition-all duration-75 text-[#12211d] font-bold`}
              onClick={() => handleAction(i + 1)}
            >
              <p className={`text-md font-bold leading-normal`}>{i + 1}</p>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

export default Cleaning;
