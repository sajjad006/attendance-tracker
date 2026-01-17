import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useSearchParams } from 'react-router-dom';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import { TrendingUp, TrendingDown, AlertTriangle, CheckCircle } from 'lucide-react';
import { Card, Select, Badge, LoadingSpinner, EmptyState } from '../components/ui';
import { analyticsApi } from '../api/analytics';
import { subjectApi } from '../api/academic';
import { useSemester } from '../context/SemesterContext';

const COLORS = ['#22c55e', '#ef4444', '#eab308'];

export default function AnalyticsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const selectedSubjectId = searchParams.get('subject');
  const { currentSemester } = useSemester();

  const { data: semesterAnalytics, isLoading: semesterLoading } = useQuery({
    queryKey: ['semester-analytics', currentSemester?.id],
    queryFn: () => analyticsApi.getSemesterAnalytics(currentSemester?.id),
    enabled: !!currentSemester,
  });

  const { data: subjects = [] } = useQuery({
    queryKey: ['subjects', currentSemester?.id],
    queryFn: () => subjectApi.getAll(currentSemester?.id),
    enabled: !!currentSemester,
  });

  const { data: subjectAnalytics, isLoading: subjectLoading } = useQuery({
    queryKey: ['subject-analytics', selectedSubjectId],
    queryFn: () => analyticsApi.getSubjectAnalytics(selectedSubjectId),
    enabled: !!selectedSubjectId,
  });

  const { data: weeklyTrends } = useQuery({
    queryKey: ['weekly-trends', selectedSubjectId],
    queryFn: () => analyticsApi.getWeeklyTrends(selectedSubjectId),
    enabled: !!selectedSubjectId,
  });

  const { data: alerts } = useQuery({
    queryKey: ['alerts', currentSemester?.id],
    queryFn: () => analyticsApi.getSemesterAlerts(currentSemester?.id),
    enabled: !!currentSemester,
  });

  if (semesterLoading) {
    return <LoadingSpinner />;
  }

  // Extract data from nested response structure
  const overview = semesterAnalytics?.overview || {};
  const overallPercentage = parseFloat(overview.overall_attendance) || 0;
  
  // Calculate totals from subjects data
  const subjectsData = semesterAnalytics?.subjects || [];
  const totalAttended = subjectsData.reduce((sum, s) => sum + (s.total_attended || 0), 0);
  const totalAbsent = subjectsData.reduce((sum, s) => sum + (s.total_absent || 0), 0);
  const totalCancelled = subjectsData.reduce((sum, s) => sum + (s.total_cancelled || 0), 0);

  const pieData = semesterAnalytics
    ? [
        { name: 'Present', value: totalAttended },
        { name: 'Absent', value: totalAbsent },
        { name: 'Cancelled', value: totalCancelled },
      ]
    : [];

  const subjectBarData = subjectsData.map((s) => ({
    name: s.subject_name?.slice(0, 10) || 'Unknown',
    percentage: parseFloat(s.attendance_percentage) || 0,
    attended: s.total_attended || 0,
    conducted: s.total_conducted || 0,
  }));

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Analytics</h1>
          <p className="text-gray-600 mt-1">
            Attendance insights for {currentSemester?.name}
          </p>
        </div>
        <Select
          value={selectedSubjectId || ''}
          onChange={(e) => {
            if (e.target.value) {
              setSearchParams({ subject: e.target.value });
            } else {
              setSearchParams({});
            }
          }}
          options={[
            { value: '', label: 'All Subjects' },
            ...subjects.map((s) => ({ value: s.id, label: s.name })),
          ]}
          className="w-48"
        />
      </div>

      {/* Overall Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Overall Attendance</p>
              <p className="text-3xl font-bold text-gray-900 mt-1">
                {overallPercentage.toFixed(1)}%
              </p>
            </div>
            <div
              className={`p-3 rounded-full ${
                overallPercentage >= 75
                  ? 'bg-green-100'
                  : 'bg-red-100'
              }`}
            >
              {overallPercentage >= 75 ? (
                <TrendingUp className="h-6 w-6 text-green-600" />
              ) : (
                <TrendingDown className="h-6 w-6 text-red-600" />
              )}
            </div>
          </div>
          <div className="mt-4">
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className={`h-2 rounded-full ${
                  overallPercentage >= 75
                    ? 'bg-green-500'
                    : 'bg-red-500'
                }`}
                style={{
                  width: `${Math.min(overallPercentage, 100)}%`,
                }}
              />
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <p className="text-sm text-gray-600">Classes Breakdown</p>
          <div className="flex items-center justify-between mt-4">
            <div className="text-center">
              <p className="text-2xl font-bold text-green-600">
                {totalAttended}
              </p>
              <p className="text-xs text-gray-500">Present</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-red-600">
                {totalAbsent}
              </p>
              <p className="text-xs text-gray-500">Absent</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-yellow-600">
                {totalCancelled}
              </p>
              <p className="text-xs text-gray-500">Cancelled</p>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <p className="text-sm text-gray-600">Status</p>
          <div className="mt-4">
            {alerts?.alerts?.length > 0 ? (
              <div className="flex items-center gap-2">
                <AlertTriangle className="h-6 w-6 text-yellow-500" />
                <div>
                  <p className="font-medium text-gray-900">
                    {alerts.alerts.length} Alert{alerts.alerts.length > 1 ? 's' : ''}
                  </p>
                  <p className="text-sm text-gray-500">
                    Some subjects need attention
                  </p>
                </div>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <CheckCircle className="h-6 w-6 text-green-500" />
                <div>
                  <p className="font-medium text-gray-900">All Good</p>
                  <p className="text-sm text-gray-500">
                    All subjects are on track
                  </p>
                </div>
              </div>
            )}
          </div>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Pie Chart */}
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Attendance Distribution
          </h3>
          {pieData.some((d) => d.value > 0) ? (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={5}
                  dataKey="value"
                  label={({ name, percent }) =>
                    `${name} ${(percent * 100).toFixed(0)}%`
                  }
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[300px] flex items-center justify-center">
              <p className="text-gray-500">No attendance data yet</p>
            </div>
          )}
        </Card>

        {/* Subject Bar Chart */}
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Subject-wise Attendance
          </h3>
          {subjectBarData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={subjectBarData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" fontSize={12} />
                <YAxis domain={[0, 100]} />
                <Tooltip
                  formatter={(value, name) => [
                    `${value}%`,
                    name === 'percentage' ? 'Attendance' : name,
                  ]}
                />
                <Bar dataKey="percentage" fill="#6366f1" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[300px] flex items-center justify-center">
              <p className="text-gray-500">No subjects to display</p>
            </div>
          )}
        </Card>
      </div>

      {/* Weekly Trends for Selected Subject */}
      {selectedSubjectId && weeklyTrends && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Weekly Trends - {weeklyTrends.subject_name}
          </h3>
          {weeklyTrends.trends?.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={weeklyTrends.trends}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="week" fontSize={12} />
                <YAxis domain={[0, 100]} />
                <Tooltip
                  formatter={(value) => [`${value}%`, 'Attendance']}
                />
                <Line
                  type="monotone"
                  dataKey="percentage"
                  stroke="#6366f1"
                  strokeWidth={2}
                  dot={{ fill: '#6366f1' }}
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[300px] flex items-center justify-center">
              <p className="text-gray-500">No weekly data available</p>
            </div>
          )}
        </Card>
      )}

      {/* Subject Details */}
      {selectedSubjectId && subjectAnalytics && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            {subjectAnalytics.subject_name} Details
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-600">Total Classes</p>
              <p className="text-2xl font-bold text-gray-900">
                {subjectAnalytics.total_conducted}
              </p>
            </div>
            <div className="p-4 bg-green-50 rounded-lg">
              <p className="text-sm text-green-600">Attended</p>
              <p className="text-2xl font-bold text-green-700">
                {subjectAnalytics.total_attended}
              </p>
            </div>
            <div className="p-4 bg-red-50 rounded-lg">
              <p className="text-sm text-red-600">Missed</p>
              <p className="text-2xl font-bold text-red-700">
                {subjectAnalytics.total_absent}
              </p>
            </div>
            <div className="p-4 bg-indigo-50 rounded-lg">
              <p className="text-sm text-indigo-600">Percentage</p>
              <p className="text-2xl font-bold text-indigo-700">
                {subjectAnalytics.attendance_percentage}%
              </p>
            </div>
          </div>

          <div className="mt-6 p-4 bg-gray-50 rounded-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">
                  Minimum Required: {subjectAnalytics.min_required_percentage}%
                </p>
                <p className="mt-1 font-medium">
                  {subjectAnalytics.status === 'safe' ? (
                    <span className="text-green-600">
                      You can miss {subjectAnalytics.classes_can_miss} more class
                      {subjectAnalytics.classes_can_miss !== 1 ? 'es' : ''}
                    </span>
                  ) : (
                    <span className="text-red-600">
                      You need to attend {subjectAnalytics.classes_need_to_attend} more class
                      {subjectAnalytics.classes_need_to_attend !== 1 ? 'es' : ''}
                    </span>
                  )}
                </p>
              </div>
              <Badge
                variant={subjectAnalytics.status === 'safe' ? 'success' : 'danger'}
              >
                {subjectAnalytics.status === 'safe' ? 'Safe' : 'At Risk'}
              </Badge>
            </div>
          </div>
        </Card>
      )}

      {/* Alerts List */}
      {alerts?.alerts?.length > 0 && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <AlertTriangle className="h-5 w-5 text-yellow-500 mr-2" />
            Attendance Alerts
          </h3>
          <div className="space-y-3">
            {alerts.alerts.map((alert, index) => (
              <div
                key={index}
                className={`p-4 rounded-lg border-l-4 ${
                  alert.type === 'danger'
                    ? 'bg-red-50 border-red-500'
                    : 'bg-yellow-50 border-yellow-500'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <p className="font-medium text-gray-900">{alert.subject_name}</p>
                    <p className="text-sm text-gray-600 mt-1">{alert.message}</p>
                  </div>
                  <Badge variant={alert.type === 'danger' ? 'danger' : 'warning'}>
                    {alert.current_percentage}%
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}
