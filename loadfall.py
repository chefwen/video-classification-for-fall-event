import numpy as np
import os
import matplotlib.pyplot as plt
from keras.utils import to_categorical
from scipy.misc import imresize

np.random.seed(1234)

def preprocess_input(x):
    if x.ndim==4:
        x[:, :, :, 0] -= 123.68
        x[:, :, :, 1] -= 116.779
        x[:, :, :, 2] -= 103.939
    else:
        x[:, :, 0] -= 123.68
        x[:, :, 1] -= 116.779
        x[:, :, 2] -= 103.939
    return x/128

def transform(img, r1):
    if r1:
        img = img[:,::-1,:]
    return img

def get_idx(num):
    # every 8 video are from the same angle, e.g. 1,9,17
    if num.size is 1:
        num = [num]
    return reduce((lambda x,y: x + range(y*8,y*8+8)), num, [])

downsample = True

# 1-184 falling down; label 0, [1,0];
idx_fall = np.random.permutation(23)
fall = {'train':get_idx(idx_fall[:14]), 'val':get_idx(idx_fall[14:18]),
        'test':get_idx(idx_fall[18:])}#23, 14,4,5

if downsample:
    # 185-224 squat 225-272 sit 273-320 lie down 321-400 walk 14,5,8
    path = './multi_small/img/'
    idx_squat = np.random.permutation(5)+23
    idx_sit = np.random.permutation(6)+23+5
    idx_lie = np.random.permutation(6)+23+5+6
    idx_walk = np.random.permutation(10)+23+5+6+6
    squat = {'train':get_idx(idx_squat[:3]), 'val':get_idx(idx_squat[3]),
            'test':get_idx(idx_squat[4])}#5, 3 1 1
    sit = {'train':get_idx(idx_sit[:3]), 'val':get_idx(idx_sit[3]),
            'test':get_idx(idx_sit[4:])}#6, 3 1 2
    lie = {'train':get_idx(idx_lie[:3]), 'val':get_idx(idx_lie[3]),
            'test':get_idx(idx_lie[4:])}#6, 3 1 2
    walk = {'train':get_idx(idx_walk[:6]), 'val':get_idx(idx_walk[6:8]),
            'test':get_idx(idx_walk[8:])}#10, 5 2 3
else:
    # sit 185-232 lie 233-264 crouch down 265-320 walk 321-400 14,5,8
    path = './multi_large/'
    idx_sit = np.random.permutation(6)+23
    idx_lie = np.random.permutation(4)+23+6
    idx_squat = np.random.permutation(7)+23+4+6
    idx_walk = np.random.permutation(10)+23+4+6+7
    sit = {'train':get_idx(idx_sit[:3]), 'val':get_idx(idx_sit[3]),
            'test':get_idx(idx_sit[4:])}#6, 3 1 2
    lie = {'train':get_idx(idx_lie[:2]), 'val':get_idx(idx_lie[2]),
            'test':get_idx(idx_lie[3])}#4, 2 1 1
    squat = {'train':get_idx(idx_squat[:4]), 'val':get_idx(idx_squat[4]),
            'test':get_idx(idx_squat[5:])}#7, 4 1 2
    walk = {'train':get_idx(idx_walk[:6]), 'val':get_idx(idx_walk[6:8]),
            'test':get_idx(idx_walk[8:])}#10, 5 2 3
#import pdb; pdb.set_trace()
class falldata:
    def __init__(self, tvt):
        self.tvt = tvt
        self.image = fall[self.tvt]+squat[self.tvt]+sit[self.tvt]+\
                lie[self.tvt]+walk[self.tvt]
        self.num = len(self.image)

    def generate(self, batch_size, shuffle=True, d2=False, multiL=False,
                 augment=False):
        #d2 means only one frame is fed

        if multiL:
            nb_classes = 5
            label = [0]*len(fall[self.tvt])+[1]*len(squat[self.tvt])+\
            [2]*len(sit[self.tvt])+[3]*len(lie[self.tvt])+[4]*len(walk[self.tvt])
        else:
            nb_classes = 2
            label = [0]*len(fall[self.tvt])+[1]*(len(self.image)-len(fall[self.tvt]))

        if shuffle:
            comb = zip(self.image,label)
            np.random.shuffle(comb)
            self.image, label = zip(*comb)

        X, y = [], []
        while True:
            for i in range(len(label)):
                assert (self.image[i]<184)!=label[i]
                temp = []
                imgs=os.listdir(path+str(self.image[i]+1).zfill(3))
                #print self.image[i]
                imgs=sorted(imgs)
                if d2:
                    #name = imgs[np.random.choice(5)]
                    name = imgs[4]
                    img = plt.imread(path+str(self.image[i]+1).zfill(3)+'/'+name)
                    temp=imresize(img, [224,224])
                else:
                    r1 = np.random.randint(2)
                    for name in imgs:
                        img = plt.imread(path+str(self.image[i]+1).zfill(3)+'/'+name)
                        if augment and self.tvt=='train':
                            img = transform(img, r1)
                        temp.append(imresize(img, [224,224]))
                # if i%10==0:
                #     plt.imshow(temp)
                #     plt.show()
                #     print(label[i])
                temp = np.float32(temp)
                #print temp.shape
                X.append(preprocess_input(temp))
                y.append(label[i])
                if len(y)==batch_size or i==len(label)-1:
                    tmp_inp = np.array(X)
                    tmp_targets = to_categorical(y,nb_classes)
                    X, y = [], []
                    yield tmp_inp, tmp_targets

    def load_all(self, shuffle=True, d2=False, multiL=False, augment=False):

        if multiL:
            nb_classes = 5
            label = [0]*len(fall[self.tvt])+[1]*len(squat[self.tvt])+\
            [2]*len(sit[self.tvt])+[3]*len(lie[self.tvt])+[4]*len(walk[self.tvt])
        else:
            nb_classes = 2
            label = [0]*len(fall[self.tvt])+[1]*(len(self.image)-len(fall[self.tvt]))

        if shuffle:
            comb = zip(self.image,label)
            np.random.shuffle(comb)
            self.image, label = zip(*comb)

        X, y = [], []
        for i in range(len(label)):
            assert (self.image[i]<184)!=label[i]
            temp = []
            imgs=os.listdir(path+str(self.image[i]+1).zfill(3))
            imgs=sorted(imgs)
            if d2:
                #name = imgs[np.random.choice(5)]
                name = imgs[4]
                img = plt.imread(path+str(self.image[i]+1).zfill(3)+'/'+name)
                temp=imresize(img, [224,224])
            else:
                r1 = np.random.randint(2)
                for name in imgs:
                    img = plt.imread(path+str(self.image[i]+1).zfill(3)+'/'+name)
                    if augment and self.tvt=='train':
                        img = transform(img, r1)
                    temp.append(imresize(img, [224,224]))
            temp = np.float32(temp)
            X.append(preprocess_input(temp))
            y.append(label[i])

        tmp_inp = np.array(X)
        tmp_targets = to_categorical(y,nb_classes)
        return tmp_inp, tmp_targets

    def get_steps(self):
        return self.num

if __name__=='__main__':
    data = falldata('val')
    gdata=data.generate(1)
    video, label = next(gdata)
    print(video.shape, label)
    plt.imshow(video[0,-1,:,:,:])
    plt.show()
