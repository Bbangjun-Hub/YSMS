import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Box,
  TextField,
  Button,
  Paper,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  CircularProgress,
  Card,
  CardContent,
  CardActions,
  Grid,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Chip
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import YouTubeIcon from '@mui/icons-material/YouTube';
import LogoutIcon from '@mui/icons-material/Logout';
import axios from 'axios';

const EditPage = () => {
  const navigate = useNavigate();
  const [subscriptions, setSubscriptions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editingSubscription, setEditingSubscription] = useState(null);
  const [deleteDialog, setDeleteDialog] = useState({ open: false, subscription: null });
  const [message, setMessage] = useState({ type: '', text: '' });
  const [formData, setFormData] = useState({
    name: '',
    youtube_channel_url: '',
    notification_time: '09:00'
  });

  const userEmail = localStorage.getItem('userEmail');

  useEffect(() => {
    if (!userEmail) {
      navigate('/login');
      return;
    }
    fetchSubscriptions();
  }, [userEmail, navigate]);

  const fetchSubscriptions = async () => {
    try {
      const response = await axios.get(`http://localhost:8000/api/subscriptions/?email=${userEmail}`);
      setSubscriptions(response.data.results || []);
    } catch (error) {
      setMessage({ 
        type: 'error', 
        text: '구독 정보를 불러오는 중 오류가 발생했습니다.' 
      });
      setSubscriptions([]);
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = (subscription) => {
    setEditingSubscription(subscription);
    setFormData({
      name: subscription.name,
      youtube_channel_url: subscription.youtube_channel_url,
      notification_time: subscription.notification_time
    });
  };

  const handleUpdate = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      await axios.put(
        `http://localhost:8000/api/subscriptions/${editingSubscription.id}/`,
        formData
      );
      
      setMessage({ 
        type: 'success', 
        text: '구독 정보가 성공적으로 수정되었습니다.' 
      });
      
      setEditingSubscription(null);
      fetchSubscriptions();
      
    } catch (error) {
      setMessage({ 
        type: 'error', 
        text: '수정 중 오류가 발생했습니다.' 
      });
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    try {
      await axios.delete(
        `http://localhost:8000/api/subscriptions/${deleteDialog.subscription.id}/`
      );
      
      setMessage({ 
        type: 'success', 
        text: '구독이 성공적으로 삭제되었습니다.' 
      });
      
      setDeleteDialog({ open: false, subscription: null });
      fetchSubscriptions();
      
    } catch (error) {
      setMessage({ 
        type: 'error', 
        text: '삭제 중 오류가 발생했습니다.' 
      });
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('userEmail');
    localStorage.removeItem('subscriptionData');
    navigate('/');
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  if (loading && subscriptions.length === 0) {
    return (
      <Container maxWidth="md" sx={{ py: 4, textAlign: 'center' }}>
        <CircularProgress />
        <Typography variant="h6" sx={{ mt: 2 }}>
          구독 정보를 불러오는 중...
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
            startIcon={<LogoutIcon />}
            onClick={handleLogout}
            color="secondary"
          >
            로그아웃
          </Button>
        </Box>
        
        <Box textAlign="center">
          <EditIcon sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
          <Typography variant="h4" component="h1" gutterBottom>
            구독 관리
          </Typography>
          <Typography variant="body1" color="text.secondary">
            {userEmail}님의 구독 목록
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

      {/* 구독 목록 */}
      {subscriptions.length === 0 ? (
        <Paper elevation={2} sx={{ p: 4, textAlign: 'center' }}>
          <YouTubeIcon sx={{ fontSize: 64, color: 'grey.400', mb: 2 }} />
          <Typography variant="h6" gutterBottom>
            등록된 구독이 없습니다
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            새로운 YouTube 채널을 구독해보세요
          </Typography>
          <Button
            variant="contained"
            onClick={() => navigate('/register')}
          >
            새 구독 등록하기
          </Button>
        </Paper>
      ) : (
        <Grid container spacing={3}>
          {subscriptions.map((subscription) => (
            <Grid item xs={12} md={6} lg={4} key={subscription.id}>
              <Card elevation={2}>
                <CardContent>
                  <Box display="flex" alignItems="center" mb={2}>
                    <YouTubeIcon sx={{ color: 'red', mr: 1 }} />
                    <Typography variant="h6" component="h3">
                      {subscription.name}
                    </Typography>
                  </Box>
                  
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                    채널: {subscription.youtube_channel_url}
                  </Typography>
                  
                  <Box display="flex" alignItems="center" gap={1} mb={2}>
                    <Chip 
                      label={`알림 시간: ${subscription.notification_time}`}
                      size="small"
                      color="primary"
                      variant="outlined"
                    />
                  </Box>
                  
                  <Typography variant="body2" color="text.secondary">
                    등록일: {new Date(subscription.created_at).toLocaleDateString()}
                  </Typography>
                </CardContent>
                
                <CardActions>
                  <Button
                    size="small"
                    startIcon={<EditIcon />}
                    onClick={() => handleEdit(subscription)}
                  >
                    수정
                  </Button>
                  <Button
                    size="small"
                    startIcon={<DeleteIcon />}
                    color="error"
                    onClick={() => setDeleteDialog({ open: true, subscription })}
                  >
                    삭제
                  </Button>
                </CardActions>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* 편집 다이얼로그 */}
      <Dialog 
        open={!!editingSubscription} 
        onClose={() => setEditingSubscription(null)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>구독 정보 수정</DialogTitle>
        <form onSubmit={handleUpdate}>
          <DialogContent>
            <Box mb={2}>
              <TextField
                fullWidth
                label="이름"
                name="name"
                value={formData.name}
                onChange={handleChange}
                required
                variant="outlined"
              />
            </Box>
            
            <Box mb={2}>
              <TextField
                fullWidth
                label="YouTube 채널 URL"
                name="youtube_channel_url"
                value={formData.youtube_channel_url}
                onChange={handleChange}
                required
                variant="outlined"
              />
            </Box>
            
            <FormControl fullWidth>
              <InputLabel>알림 시간</InputLabel>
              <Select
                name="notification_time"
                value={formData.notification_time}
                onChange={handleChange}
                label="알림 시간"
              >
                <MenuItem value="06:00">오전 6시</MenuItem>
                <MenuItem value="06:30">오전 6시 30분</MenuItem>
                <MenuItem value="07:00">오전 7시</MenuItem>
                <MenuItem value="07:30">오전 7시 30분</MenuItem>
                <MenuItem value="08:00">오전 8시</MenuItem>
                <MenuItem value="08:30">오전 8시 30분</MenuItem>
                <MenuItem value="09:00">오전 9시</MenuItem>
                <MenuItem value="09:30">오전 9시 30분</MenuItem>
                <MenuItem value="10:00">오전 10시</MenuItem>
                <MenuItem value="10:30">오전 10시 30분</MenuItem>
                <MenuItem value="11:00">오전 11시</MenuItem>
                <MenuItem value="11:30">오전 11시 30분</MenuItem>
                <MenuItem value="12:00">오후 12시</MenuItem>
                <MenuItem value="12:30">오후 12시 30분</MenuItem>
                <MenuItem value="13:00">오후 1시</MenuItem>
                <MenuItem value="13:30">오후 1시 30분</MenuItem>
                <MenuItem value="14:00">오후 2시</MenuItem>
                <MenuItem value="14:30">오후 2시 30분</MenuItem>
                <MenuItem value="15:00">오후 3시</MenuItem>
                <MenuItem value="15:30">오후 3시 30분</MenuItem>
                <MenuItem value="16:00">오후 4시</MenuItem>
                <MenuItem value="16:30">오후 4시 30분</MenuItem>
                <MenuItem value="17:00">오후 5시</MenuItem>
                <MenuItem value="17:30">오후 5시 30분</MenuItem>
                <MenuItem value="18:00">오후 6시</MenuItem>
                <MenuItem value="18:30">오후 6시 30분</MenuItem>
                <MenuItem value="19:00">오후 7시</MenuItem>
                <MenuItem value="19:30">오후 7시 30분</MenuItem>
                <MenuItem value="20:00">오후 8시</MenuItem>
                <MenuItem value="20:30">오후 8시 30분</MenuItem>
                <MenuItem value="21:00">오후 9시</MenuItem>
                <MenuItem value="21:30">오후 9시 30분</MenuItem>
                <MenuItem value="22:00">오후 10시</MenuItem>
                <MenuItem value="22:30">오후 10시 30분</MenuItem>
              </Select>
            </FormControl>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setEditingSubscription(null)}>
              취소
            </Button>
            <Button type="submit" variant="contained" disabled={loading}>
              {loading ? '수정 중...' : '수정'}
            </Button>
          </DialogActions>
        </form>
      </Dialog>

      {/* 삭제 확인 다이얼로그 */}
      <Dialog
        open={deleteDialog.open}
        onClose={() => setDeleteDialog({ open: false, subscription: null })}
      >
        <DialogTitle>구독 삭제 확인</DialogTitle>
        <DialogContent>
          <Typography>
            정말로 "{deleteDialog.subscription?.name}" 구독을 삭제하시겠습니까?
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            이 작업은 되돌릴 수 없습니다.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialog({ open: false, subscription: null })}>
            취소
          </Button>
          <Button onClick={handleDelete} color="error" variant="contained">
            삭제
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default EditPage; 