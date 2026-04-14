import { Navigate } from 'react-router-dom';
import { isAuthenticated } from '../api/auth.js';

/**
 * ProtectedRoute component that redirects to login if not authenticated.
 *
 * Usage:
 *   <Route path="/protected" element={
 *     <ProtectedRoute>
 *       <ProtectedComponent />
 *     </ProtectedRoute>
 *   } />
 */
export default function ProtectedRoute({ children }) {
  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }

  return children;
}
