import StudentStatsCard from './widgets/StudentStatsCard';
import StudentTableWidget from './widgets/StudentTableWidget';
import AdminStudentsWidget from './widgets/AdminStudentsWidget';
import ReportsChartWidget from './widgets/ReportsChartWidget';
import AdminUsersWidget from './widgets/AdminUsersWidget';
import AdminRolesWidget from './widgets/AdminRolesWidget';
import AuditLogWidget from './widgets/AuditLogWidget';

// Maps backend component_key → React component
const WIDGET_MAP = {
  StudentStatsCard,
  StudentTableWidget,
  AdminStudentsWidget,
  ReportsChartWidget,
  AdminUsersWidget,
  AdminRolesWidget,
  AuditLogWidget,
};

export default function DashboardGrid({ widgets }) {
  return (
    <div className="grid grid-cols-[repeat(auto-fit,minmax(280px,1fr))] gap-6 auto-rows-[minmax(350px,auto)] md:grid-cols-[repeat(auto-fit,minmax(350px,1fr))]">
      {widgets.map((widget) => {
        const Component = WIDGET_MAP[widget.component_key];
        if (!Component) return null;
        
        // Let's determine column span based on widget type
        // Tables usually need more space
        let spanClass = "col-span-1";
        if (widget.widget_type === 'table') {
           spanClass = "md:col-span-2";
        }
        
        return (
          <div
            key={widget.id}
            className={`flex flex-col h-full ${spanClass}`}
            id={`widget-${widget.name}`}
          >
            <Component widget={widget} />
          </div>
        );
      })}
    </div>
  );
}
