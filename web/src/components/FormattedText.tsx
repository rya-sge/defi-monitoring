import { Children, cloneElement, isValidElement } from 'react';
import type { ReactNode } from 'react';
import { shortHash } from '../lib/format';

/** Dim decimal digits, compact suffixes, percent signs and trailing units without changing their spelling. */
export function FormattedText({
  children,
  mutedUnits = true,
}: {
  children: ReactNode;
  mutedUnits?: boolean;
}) {
  return Children.map(children, (child): ReactNode => {
    if (typeof child === 'string') {
      const text = child.replace(/0x[\da-fA-F]{40,64}\b/g, (address) => shortHash(address));
      return text
        .split(
          /(%|(?<![.])\.\d+[KMBGT]?(?![\da-fA-F])|(?<=\d)[KMBGT]\b|(?<=\d[KMBGT%]?\s+)[A-Z]{2}[A-Za-z\d]*(?:[-/][A-Za-z\d]+)*\b)/g,
        )
        .map((part, index) =>
          part === '%' ||
          /^(?:\.\d+[KMBGT]?|[KMBGT])$/.test(part) ||
          (mutedUnits && index % 2 === 1 && /^[A-Z]{2}/.test(part)) ? (
            <span key={index} className="text-muted-foreground">
              {part}
            </span>
          ) : (
            part
          ),
        );
    }
    if (
      isValidElement<{ children?: ReactNode }>(child) &&
      typeof child.type === 'string' &&
      child.props.children != null
    ) {
      return cloneElement(
        child,
        {},
        <FormattedText mutedUnits={mutedUnits}>{child.props.children}</FormattedText>,
      );
    }
    return child;
  });
}
