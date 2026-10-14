import type { RouteObject } from 'react-router'

import { AppLayout } from '../components/layout/AppLayout'
import { AdminPage } from '../pages/AdminPage'
import { DashboardPage } from '../pages/DashboardPage'
import { GroceryListPage } from '../pages/GroceryListPage'
import { HelpPage } from '../pages/HelpPage'
import { HomePage } from '../pages/HomePage'
import { LoginPage } from '../pages/LoginPage'
import { MealDetailsPage } from '../pages/MealDetailsPage'
import { MealPlanPage } from '../pages/MealPlanPage'
import { NotFoundPage } from '../pages/NotFoundPage'
import { ProfilePage } from '../pages/ProfilePage'
import { RegisterPage } from '../pages/RegisterPage'
import { GuestOnly, RequireAdmin, RequireAuth } from './guards'
import { RootProviders } from './RootProviders'

/** Route table shared by the browser router and the tests. */
export const routes: RouteObject[] = [
  {
    element: <RootProviders />,
    children: [
      {
        path: '/',
        element: <AppLayout />,
        children: [
          { index: true, element: <HomePage /> },
          { path: 'help', element: <HelpPage /> },
          { path: 'login', element: <GuestOnly><LoginPage /></GuestOnly> },
          { path: 'register', element: <GuestOnly><RegisterPage /></GuestOnly> },
          { path: 'profile', element: <RequireAuth><ProfilePage /></RequireAuth> },
          { path: 'meal-plan', element: <RequireAuth><MealPlanPage /></RequireAuth> },
          { path: 'meal-plan/meals/:mealId', element: <RequireAuth><MealDetailsPage /></RequireAuth> },
          { path: 'grocery-list', element: <RequireAuth><GroceryListPage /></RequireAuth> },
          { path: 'dashboard', element: <RequireAuth><DashboardPage /></RequireAuth> },
          { path: 'admin', element: <RequireAdmin><AdminPage /></RequireAdmin> },
          { path: '*', element: <NotFoundPage /> },
        ],
      },
    ],
  },
]
