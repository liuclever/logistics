import type { ReactNode } from 'react';

interface WorkbenchShellProps {
  sidebar: ReactNode;
  center: ReactNode;
  trace: ReactNode;
}

export function WorkbenchShell({ sidebar, center, trace }: WorkbenchShellProps) {
  return (
    <section className="workbench-shell">
      <aside className="workbench-panel sidebar-panel">{sidebar}</aside>
      <section className="workbench-panel center-panel">{center}</section>
      <aside className="workbench-panel trace-panel">{trace}</aside>
    </section>
  );
}
