import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import {
  CheckCircle,
  XCircle,
  AlertTriangle,
  TrendingUp,
  Calendar,
  BookOpen,
  ArrowRight,
} from 'lucide-react';
import { format } from 'date-fns';
import { Card, Badge, LoadingSpinner, EmptyState, Button } from '../components/ui';
import { analyticsApi } from '../api/analytics';
import { attendanceApi } from '../api/attendance';
import { useSemester } from '../context/SemesterContext';

export default function DashboardPage() {
  const { currentSemester } = useSemester();

  const { data: dashboard, isLoading: dashboardLoading } = useQuery({
    queryKey: ['dashboard', currentSemester?.id],
    queryFn: () => analyticsApi.getDashboard(currentSemester?.id),
    enabled: !!currentSemester,
  });

  const { data: todayAttendance, isLoading: todayLoading } = useQuery({
    queryKey: ['today-attendance', currentSemester?.id],
    queryFn: () => attendanceApi.getToday(currentSemester?.id),
    enabled: !!currentSemester,
  });

  if (!currentSemester) {
    return (
      <EmptyState
        icon={Calendar}
        title="No Semester Selected"
        description="Create a semester to start tracking your attendance"
        action={
          <Link to="/settings">
            <Button>Create Semester</Button>
          </Link>
        }
      />
    );
  }

  if (dashboardLoading) {
    return <LoadingSpinner />;
  }

  // Extract data from nested response structure
  const overview = dashboard?.overview || {};
  const overallPercentage = parseFloat(overview.overall_attendance) || 0;
  const subjectsData = dashboard?.subjects || [];
  
  // Calculate totals from subjects data
  const totalAttended = subjectsData.reduce((sum, s) => sum + (s.total_attended || 0), 0);
  const totalAbsent = subjectsData.reduce((sum, s) => sum + (s.total_absent || 0), 0);
  const totalConducted = subjectsData.reduce((sum, s) => sum + (s.total_conducted || 0), 0);

  const stats = [
    {
      name: 'Overall Attendance',
      value: `${overallPercentage.toFixed(1)}%`,
      icon: TrendingUp,
      color: 'text-indigo-600',
      bgColor: 'bg-indigo-100',
    },
    {
      name: 'Classes Attended',
      value: totalAttended,
      icon: CheckCircle,
      color: 'text-green-600',
      bgColor: 'bg-green-100',
    },
    {
      name: 'Classes Missed',
      value: totalAbsent,
      icon: XCircle,
      color: 'text-red-600',
      bgColor: 'bg-red-100',
    },
    {
      name: 'Total Classes',
      value: totalConducted,
      icon: BookOpen,
      color: 'text-blue-600',
      bgColor: 'bg-blue-100',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600 mt-1">
          {currentSemester?.name} • {format(new Date(), 'EEEE, MMMM d, yyyy')}
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat) => (
          <Card key={stat.name} className="p-6">
            <div className="flex items-center">
              <div className={`p-3 rounded-lg ${stat.bgColor}`}>
                <stat.icon className={`h-6 w-6 ${stat.color}`} />
              </div>
              <div className="ml-4">
                <p className="text-sm text-gray-600">{stat.name}</p>
                <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
              </div>
            </div>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Today's Classes */}
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Today's Classes</h2>
            <Link to="/attendance" className="text-sm text-indigo-600 hover:text-indigo-700 flex items-center">
              View all <ArrowRight className="h-4 w-4 ml-1" />
            </Link>
          </div>
          {todayLoading ? (
            <LoadingSpinner size="sm" />
          ) : todayAttendance?.records?.length > 0 ? (
            <div className="space-y-3">
              {todayAttendance.records.map((record) => (
                <div
                  key={record.id}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                >
                  <div>
                    <p className="font-medium text-gray-900">{record.subject_name}</p>
                    <p className="text-sm text-gray-500">
                      {record.start_time} - {record.end_time}
                    </p>
                  </div>
                  <Badge
                    variant={
                      record.status === 'present'
                        ? 'success'
                        : record.status === 'absent'
                        ? 'danger'
                        : 'warning'
                    }
                  >
                    {record.status}
                  </Badge>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 text-center py-8">No classes scheduled for today</p>
          )}
        </Card>

        {/* Subject Overview */}
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Subject Overview</h2>
            <Link to="/subjects" className="text-sm text-indigo-600 hover:text-indigo-700 flex items-center">
              View all <ArrowRight className="h-4 w-4 ml-1" />
            </Link>
          </div>
          {subjectsData.length > 0 ? (
            <div className="space-y-3">
              {subjectsData.slice(0, 5).map((subject) => {
                const percentage = parseFloat(subject.attendance_percentage) || 0;
                return (
                  <div key={subject.subject_id} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-gray-900">
                        {subject.subject_name}
                      </span>
                      <span
                        className={`text-sm font-medium ${
                          percentage >= 75
                            ? 'text-green-600'
                            : percentage >= 50
                            ? 'text-yellow-600'
                            : 'text-red-600'
                        }`}
                      >
                        {percentage.toFixed(1)}%
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full ${
                          percentage >= 75
                            ? 'bg-green-500'
                            : percentage >= 50
                            ? 'bg-yellow-500'
                            : 'bg-red-500'
                        }`}
                        style={{ width: `${Math.min(percentage, 100)}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <p className="text-gray-500 text-center py-8">No subjects added yet</p>
          )}
        </Card>
      </div>

      {/* Alerts */}
      {dashboard?.alerts?.length > 0 && (
        <Card className="p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <AlertTriangle className="h-5 w-5 text-yellow-500 mr-2" />
            Attendance Alerts
          </h2>
          <div className="space-y-3">
            {dashboard.alerts.map((alert, index) => (
              <div
                key={index}
                className={`p-4 rounded-lg border-l-4 ${
                  alert.type === 'danger'
                    ? 'bg-red-50 border-red-500'
                    : 'bg-yellow-50 border-yellow-500'
                }`}
              >
                <p className="text-sm font-medium text-gray-900">{alert.subject_name}</p>
                <p className="text-sm text-gray-600 mt-1">{alert.message}</p>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}
