import { useChineseMode } from "@/context/ChineseModeContext";

export function ChineseModeToggle() {
  const { mode, toggleMode } = useChineseMode();

  const isTraditional = mode === "traditional";

  return (
    <button
      onClick={toggleMode}
      className="
        relative w-18 h-10
        rounded-full
        bg-gray-200
        flex items-center
        px-1
        transition-colors duration-300
        focus:outline-none
      "
    >
      {/* sliding pill */}
      <div
        className={`
          absolute top-1 bottom-1 left-1
          w-8
          rounded-full
          bg-white
          shadow-md
          transition-transform duration-300 ease-in-out
          ${isTraditional ? "translate-x-8" : "translate-x-0"}
        `}
      />

      {/* labels */}
      <div className="relative z-10 flex w-full justify-between text-md font-medium px-2">
        <span className={isTraditional ? "text-gray-400" : "text-black"}>
          简
        </span>
        <span className={isTraditional ? "text-black" : "text-gray-400"}>
          繁
        </span>
      </div>
    </button>
  );
}
