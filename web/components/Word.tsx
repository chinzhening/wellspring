interface WordProps {
  surface: string;
}

export function Word({ surface }: WordProps) {
  const isSpace = surface === " ";

  return (
    <div className="inline-flex flex-col items-center">
      <div className="mb-1 h-5">&nbsp;</div>

      {isSpace ? (
        <span
          className="inline-block text-2xl lg:text-4xl leading-none"
          style={{ width: "0.5em" }} // adjust to taste
          aria-hidden="true"
        />
      ) : (
        <span className="text-xl lg:text-2xl leading-none">
          {surface}
        </span>
      )}
    </div>
  );
}