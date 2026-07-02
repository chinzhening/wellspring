interface WordProps {
  surface: string;
}

export function Word({ surface }: WordProps) {
  const isSpace = surface === " ";

  return (
    <span className="grid grid-row-1 select-none pt-6 lg:pt-9">
      <span
        className="
        leading-none
        text-[16px] lg:text-[24px]
        uppercase tracking-[0.22em] "
        aria-hidden={isSpace}
      >
        {isSpace ? " " : surface}
      </span>
    </span>
  );
}
