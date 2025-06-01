import React, { useState } from 'react';
import {
  Container,
  Typography,
  Box,
  TextField,
  Button,
  Paper,
  Alert,
  CircularProgress
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import AdminPanelSettingsIcon from '@mui/icons-material/AdminPanelSettings';
import axios from 'axios';

const AdminLoginPage = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    username: '',
    password: ''
  });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage({ type: '', text: '' });

    try {
      const response = await axios.post('http://localhost:8000/api/subscriptions/auth/admin-login/', formData);
      
      if (response.data.message === '관리자 로그인 성공') {
        // 관리자 정보를 로컬 스토리지에 저장
        localStorage.setItem('adminToken', 'admin-authenticated');
        localStorage.setItem('adminUser', JSON.stringify(response.data.user));
        
        setMessage({ 
          type: 'success', 
          text: '관리자 로그인 성공! 관리자 페이지로 이동합니다.' 
        });
        
        // 2초 후 관리자 페이지로 이동
        setTimeout(() => {
          navigate('/admin');
        }, 2000);
      }
      
    } catch (error) {
      setMessage({ 
        type: 'error', 
        text: error.response?.data?.username?.[0] || 
              error.response?.data?.password?.[0] || 
              error.response?.data?.non_field_errors?.[0] ||
              '관리자 로그인 중 오류가 발생했습니다.' 
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="sm" sx={{ py: 4 }}>
      {/* 헤더 */}
      <Box mb={4}>
        <Button
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate('/')}
          sx={{ mb: 2 }}
        >
          홈으로 돌아가기
        </Button>
        
        <Box textAlign="center">
          <AdminPanelSettingsIcon sx={{ fontSize: 48, color: 'warning.main', mb: 2 }} />
          <Typography variant="h4" component="h1" gutterBottom>
            관리자 로그인
          </Typography>
          <Typography variant="body1" color="text.secondary">
            시스템 관리를 위한 관리자 로그인
          </Typography>
        </Box>
      </Box>

      {/* 로그인 폼 */}
      <Paper elevation={3} sx={{ p: 4 }}>
        <form onSubmit={handleSubmit}>
          <Box mb={3}>
            <TextField
              fullWidth
              label="관리자 아이디"
              name="username"
              value={formData.username}
              onChange={handleChange}
              required
              variant="outlined"
              autoFocus
            />
          </Box>

          <Box mb={3}>
            <TextField
              fullWidth
              label="비밀번호"
              name="password"
              type="password"
              value={formData.password}
              onChange={handleChange}
              required
              variant="outlined"
            />
          </Box>

          <Box textAlign="center">
            <Button
              type="submit"
              variant="contained"
              color="warning"
              size="large"
              disabled={loading}
              startIcon={<AdminPanelSettingsIcon />}
              sx={{ minWidth: 200 }}
            >
              {loading ? (
                <>
                  <CircularProgress size={20} sx={{ mr: 1 }} />
                  로그인 중...
                </>
              ) : (
                '관리자 로그인'
              )}
            </Button>
          </Box>
        </form>

        {message.text && (
          <Box mt={3}>
            <Alert severity={message.type}>
              {message.text}
            </Alert>
          </Box>
        )}
      </Paper>

      {/* 안내 사항 */}
      <Box mt={4}>
        <Paper elevation={1} sx={{ p: 3, backgroundColor: 'grey.50' }}>
          <Typography variant="h6" gutterBottom>
            🔐 관리자 로그인 안내
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            • 관리자는 모든 구독을 관리하고 통계를 확인할 수 있습니다
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            • 테스트 이메일 발송 및 시스템 관리 기능을 제공합니다
          </Typography>
          <Typography variant="body2" color="text.secondary">
            • 보안을 위해 세션은 일정 시간 후 자동으로 만료됩니다
          </Typography>
        </Paper>
      </Box>

      {/* 추가 액션 */}
      <Box mt={3} textAlign="center">
        <Button
          variant="text"
          onClick={() => navigate('/login')}
          size="small"
        >
          구독자 로그인으로 돌아가기
        </Button>
      </Box>
    </Container>
  );
};

export default AdminLoginPage; 