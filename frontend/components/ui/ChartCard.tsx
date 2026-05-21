"use client";

interface Props {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
  className?: string;
}

export function ChartCard({ title, subtitle, children, className = "" }: Props) {
  return (
    <div className={`bg-[#1e293b] border border-[#334155] rounded-xl p-5 ${className}`}>
      <div className="mb-4">
        <h3 className="text-slate-200 font-semibold">{title}</h3>
        {subtitle && <p className="text-slate-500 text-sm mt-0.5">{subtitle}</p>}
      </div>
      {children}
    </div>
  );
}
