import { separatePinyin, toneText } from "@/lib/pinyin";

interface ChineseCharacterProps {
  simplified: string;
  traditional: string;
  pinyin: string;
  traditionalMode: boolean;
  showPinyin: boolean;
}

export function ChineseCharacter({
  simplified,
  traditional,
  pinyin,
  traditionalMode,
  showPinyin,
}: ChineseCharacterProps) {
  return (
    <div className="inline-flex flex-col items-center select-none">
      {/* Pinyin display */}
      <div
        className="mb-1 h-3 lg:h-5 text-xs lg:text-sm font-medium text-text-secondary"
        style={{ visibility: showPinyin ? "visible" : "hidden" }}>
        {separatePinyin(toneText(pinyin))}
      </div>

      <span className="text-2xl lg:text-4xl leading-none text-text-primary">
        {traditionalMode ? traditional : simplified}
      </span>
    </div>
  );
}