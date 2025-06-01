import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Box,
  Button,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Alert,
  CircularProgress,
  Card,
  CardContent,
  Grid,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import AdminPanelSettingsIcon from '@mui/icons-material/AdminPanelSettings';
import PeopleIcon from '@mui/icons-material/People';
import EmailIcon from '@mui/icons-material/Email';
import YouTubeIcon from '@mui/icons-material/YouTube';
import SendIcon from '@mui/icons-material/Send';
import DeleteIcon from '@mui/icons-material/Delete';
import RefreshIcon from '@mui/icons-material/Refresh';
import axios from 'axios';

const AdminPage = () => {
  const navigate = useNavigate();
  const [subscriptions, setSubscriptions] = useState([]);
  const [stats, setStats] = useState({
    total_subscriptions: 0,
    active_subscriptions: 0,
    total_emails_sent: 0
  });
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState({ type: '', text: '' });
  const [testEmailOpen, setTestEmailOpen] = useState(false);
  const [testEmailData, setTestEmailData] = useState({
    email: '',
    subject: '',
    message: ''
  });
  const [isProcessingYoutube, setIsProcessingYoutube] = useState(false);

  useEffect(() => {
    // 관리자 인증 체크
    const adminToken = localStorage.getItem('adminToken');
    const adminUser = localStorage.getItem('adminUser');
    
    if (!adminToken || !adminUser) {
      setMessage({ 
        type: 'error', 
        text: '관리자 권한이 필요합니다. 로그인 페이지로 이동합니다.' 
      });
      setTimeout(() => {
        navigate('/login');
      }, 2000);
      return;
    }

    fetchData();
  }, [navigate]);

  const fetchData = async () => {
    try {
      // 구독 목록 가져오기
      const subscriptionsResponse = await axios.get('http://localhost:8000/api/subscriptions/admin/subscriptions/');
      setSubscriptions(subscriptionsResponse.data);

      // 통계 가져오기
      const statsResponse = await axios.get('http://localhost:8000/api/subscriptions/admin/stats/');
      setStats(statsResponse.data);

    } catch (error) {
      if (error.response?.status === 403 || error.response?.status === 401) {
        setMessage({ 
          type: 'error', 
          text: '관리자 권한이 없습니다. 로그인 페이지로 이동합니다.' 
        });
        localStorage.removeItem('adminToken');
        localStorage.removeItem('adminUser');
        setTimeout(() => {
          navigate('/login');
        }, 2000);
      } else {
        setMessage({ 
          type: 'error', 
          text: '데이터를 불러오는 중 오류가 발생했습니다.' 
        });
      }
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteSubscription = async (subscriptionId) => {
    if (!window.confirm('정말로 이 구독을 삭제하시겠습니까?')) {
      return;
    }

    try {
      await axios.delete(`http://localhost:8000/api/subscriptions/admin/subscriptions/${subscriptionId}/`);
      setMessage({ 
        type: 'success', 
        text: '구독이 성공적으로 삭제되었습니다.' 
      });
      fetchData();
    } catch (error) {
      setMessage({ 
        type: 'error', 
        text: '삭제 중 오류가 발생했습니다.' 
      });
    }
  };

  const handleSendTestEmail = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/subscriptions/admin/send-test-email/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(testEmailData),
      });

      const data = await response.json();
      
      if (data.success) {
        setMessage({ type: 'success', text: '테스트 이메일이 성공적으로 발송되었습니다.' });
        setTestEmailOpen(false);
        setTestEmailData({ email: '', subject: '', message: '' });
      } else {
        setMessage({ type: 'error', text: `테스트 이메일 발송 실패: ${data.message}` });
      }
    } catch (error) {
      setMessage({ type: 'error', text: '테스트 이메일 발송 중 오류가 발생했습니다.' });
    }
  };

  const handleProcessYoutubeSummaries = async () => {
    setIsProcessingYoutube(true);
    setMessage({ type: 'info', text: 'YouTube 요약 처리를 시작합니다...' });
    
    try {
      const response = await fetch('http://localhost:8000/api/subscriptions/admin/process-youtube-summaries/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      const data = await response.json();
      
      if (data.success) {
        setMessage({ 
          type: 'success', 
          text: `YouTube 요약 처리 완료: ${data.processed_count}개 구독자에게 발송, ${data.channels_found}개 채널 처리` 
        });
      } else {
        setMessage({ type: 'error', text: `YouTube 요약 처리 실패: ${data.message}` });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'YouTube 요약 처리 중 오류가 발생했습니다.' });
    } finally {
      setIsProcessingYoutube(false);
    }
  };

  const handleTestEmailChange = (e) => {
    setTestEmailData({
      ...testEmailData,
      [e.target.name]: e.target.value
    });
  };

  const handleLogout = () => {
    localStorage.removeItem('adminToken');
    localStorage.removeItem('adminUser');
    setMessage({ 
      type: 'success', 
      text: '로그아웃되었습니다.' 
    });
    setTimeout(() => {
      navigate('/');
    }, 1000);
  };

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ py: 4, textAlign: 'center' }}>
        <CircularProgress />
        <Typography variant="h6" sx={{ mt: 2 }}>
          관리자 데이터를 불러오는 중...
        </Typography>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* 헤더 */}
      <Box mb={4}>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Button
            startIcon={<ArrowBackIcon />}
            onClick={() => navigate('/')}
          >
            홈으로 돌아가기
          </Button>
          
          <Button
            variant="outlined"
            color="error"
            onClick={handleLogout}
          >
            로그아웃
          </Button>
        </Box>
        
        <Box textAlign="center">
          <AdminPanelSettingsIcon sx={{ fontSize: 48, color: 'warning.main', mb: 2 }} />
          <Typography variant="h4" component="h1" gutterBottom>
            관리자 대시보드
          </Typography>
          <Typography variant="body1" color="text.secondary">
            YouTube 메일링 서비스 관리
          </Typography>
        </Box>
      </Box>

      {message.text && (
        <Box mb={3}>
          <Alert severity={message.type} onClose={() => setMessage({ type: '', text: '' })}>
            {message.text}
          </Alert>
        </Box>
      )}

      {/* 통계 카드 */}
      <Grid container spacing={3} mb={4}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <PeopleIcon sx={{ fontSize: 48, color: 'primary.main', mb: 1 }} />
              <Typography variant="h4" component="div">
                {stats.total_subscriptions}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                총 구독자 수
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <YouTubeIcon sx={{ fontSize: 48, color: 'error.main', mb: 1 }} />
              <Typography variant="h4" component="div">
                {stats.active_subscriptions}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                활성 구독 수
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <EmailIcon sx={{ fontSize: 48, color: 'success.main', mb: 1 }} />
              <Typography variant="h4" component="div">
                {stats.total_emails_sent}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                발송된 이메일 수
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* 관리 액션 */}
      <Box mb={4}>
        <Paper elevation={2} sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            관리 작업
          </Typography>
          <Box display="flex" gap={2} flexWrap="wrap">
            <Button
              variant="contained"
              startIcon={<SendIcon />}
              onClick={() => setTestEmailOpen(true)}
            >
              테스트 이메일 발송
            </Button>
            <Button
              variant="contained"
              color="success"
              startIcon={<YouTubeIcon />}
              onClick={handleProcessYoutubeSummaries}
              disabled={isProcessingYoutube}
            >
              {isProcessingYoutube ? 'YouTube 요약 처리 중...' : 'YouTube 요약 처리'}
            </Button>
            <Button
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={fetchData}
            >
              데이터 새로고침
            </Button>
          </Box>
        </Paper>
      </Box>

      {/* 구독 목록 테이블 */}
      <Paper elevation={2}>
        <Box p={3}>
          <Typography variant="h6" gutterBottom>
            전체 구독 목록
          </Typography>
          
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>ID</TableCell>
                  <TableCell>이름</TableCell>
                  <TableCell>이메일</TableCell>
                  <TableCell>YouTube 채널</TableCell>
                  <TableCell>알림 시간</TableCell>
                  <TableCell>등록일</TableCell>
                  <TableCell>상태</TableCell>
                  <TableCell>작업</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {subscriptions.map((subscription) => (
                  <TableRow key={subscription.id}>
                    <TableCell>{subscription.id}</TableCell>
                    <TableCell>{subscription.name}</TableCell>
                    <TableCell>{subscription.email}</TableCell>
                    <TableCell>
                      <Typography variant="body2" sx={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                        {subscription.youtube_channel_url}
                      </Typography>
                    </TableCell>
                    <TableCell>{subscription.notification_time}</TableCell>
                    <TableCell>
                      {new Date(subscription.created_at).toLocaleDateString()}
                    </TableCell>
                    <TableCell>
                      <Chip 
                        label={subscription.is_active ? '활성' : '비활성'}
                        color={subscription.is_active ? 'success' : 'default'}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      <Button
                        size="small"
                        startIcon={<DeleteIcon />}
                        color="error"
                        onClick={() => handleDeleteSubscription(subscription.id)}
                      >
                        삭제
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
          
          {subscriptions.length === 0 && (
            <Box textAlign="center" py={4}>
              <Typography variant="body1" color="text.secondary">
                등록된 구독이 없습니다.
              </Typography>
            </Box>
          )}
        </Box>
      </Paper>

      {/* 테스트 이메일 다이얼로그 */}
      <Dialog 
        open={testEmailOpen} 
        onClose={() => setTestEmailOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>테스트 이메일 발송</DialogTitle>
        <DialogContent>
          <Box mb={2}>
            <TextField
              fullWidth
              label="받는 사람 이메일"
              name="email"
              type="email"
              value={testEmailData.email}
              onChange={handleTestEmailChange}
              required
              variant="outlined"
              margin="normal"
            />
          </Box>
          
          <Box mb={2}>
            <TextField
              fullWidth
              label="제목"
              name="subject"
              value={testEmailData.subject}
              onChange={handleTestEmailChange}
              required
              variant="outlined"
              margin="normal"
            />
          </Box>
          
          <TextField
            fullWidth
            label="메시지"
            name="message"
            value={testEmailData.message}
            onChange={handleTestEmailChange}
            required
            variant="outlined"
            margin="normal"
            multiline
            rows={4}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setTestEmailOpen(false)}>
            취소
          </Button>
          <Button onClick={handleSendTestEmail} variant="contained">
            발송
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default AdminPage; 