import torch
import torch.nn as nn
import numpy as np
import torch.optim as optim
from torch.autograd import Variable
import json
import h5py
import random

def get_batches():
    batch_start = 0
    batch_end = batch_size
    random.shuffle(sample_idx)
    losses = []
    all_train_batches = []
    all_label_batches = []
    count = 0
    while (batch_end <= no_training_samples):
       #print batch_end
       #print 'ok ',count
       #print sample_idx
       idx = sample_idx[batch_start:batch_end]
       #print idx
       this_train_batch = []
       this_label_batch = []
       this_train_batch = [train[id] for id in idx]
       this_label_batch = [labels[id] for id in idx]
       all_train_batches.append(this_train_batch)
       all_label_batches.append(this_label_batch)
       if batch_end == no_training_samples:
          break
       batch_start += batch_size
       batch_end = min(batch_end + batch_size, no_training_samples)
       count += 1
    if len(all_train_batches) == len(all_label_batches):
       print 'Batch sampling complete'
    else:
       print 'Batch sizes unequal'
    return (all_train_batches,all_label_batches)


att = h5py.File('att_vgg_color.h5')
att_test = h5py.File('att_vgg_color_test.h5')
obj = json.load(open('raw_train_color.json','r'))
obj_test = json.load(open('raw_test_color.json','r'))
train = []
test = []
labels = []
no_training_samples = 35000
no_test_samples = 10000
#no_test_samples = att_test['maps_with_vgg'].shape[0]
batch_size = 100
sample_idx = range(no_training_samples)
#for i in range(att['maps_with_vgg'].shape[0]):
for i in range(no_training_samples):
  label = np.zeros([12]).astype('int')	
  train.append(att['maps_with_vgg'][i])
  label[obj[i]['color_id']] = 1
  labels.append(label)

for k in range(no_test_samples):
  test.append(att_test['maps_with_vgg'][k])

class _classifier(nn.Module):
    def __init__(self, featureDim , nTargets):
        super(_classifier, self).__init__()
        self.main = nn.Sequential(
        	nn.Linear(featureDim,1024),
                #nn.Dropout(),
        	nn.ReLU(),
                nn.Linear(1024,512),
                nn.Dropout(),
                nn.ReLU(),
                nn.Linear(512, nTargets),
        
        )

    def forward(self, input):
        return self.main(input)

no_classes = len(labels[0]) # 3 target classes, for us it is equal to no. of objects.
feature_dim = 512
classifier = _classifier(feature_dim,no_classes)
print classifier 
optimizer = optim.Adam(classifier.parameters(), weight_decay = 5e-4)
criterion = nn.MultiLabelSoftMarginLoss()

epochs = 40

(T,L) = get_batches()
#print sample_idx 
#print labels[sample_idx[0]]
for epoch in range(epochs):
    losses = []
    correct_count = 0
    correct_test = []
    for j in range(no_test_samples):
       y = test[j]
       input = Variable(torch.FloatTensor(y)).view(1,-1)
       predicted = classifier(input)
       #out = torch.sigmoid(predicted).data > 0.2
       maxim,idx = torch.max(torch.sigmoid(predicted).data,1)
       if idx[0]==obj_test[j]['color_id']:
         correct_count += 1

    correct_test.append(correct_count)
    print 'Test set correct out of 10K:', correct_count
    for i in range(len(T)):
       #print len(T[i])
       #print len(L[i])
       #print T[i][0]
       labelsv = Variable(torch.FloatTensor(L[i])).view(batch_size, -1)
       #print labelsv
       inputv = Variable(torch.FloatTensor(torch.from_numpy(np.array(T[i])))).view(batch_size, -1)
       
        
       output = classifier(inputv)
       loss = criterion(output, labelsv)

       optimizer.zero_grad()
       loss.backward()
       optimizer.step()
       losses.append(loss.data.mean())

    print('[%d/%d] Loss: %.3f' % (epoch+1, epochs, np.mean(losses)))

trained_model = torch.save(classifier,'trained2_color_35000.t7')

classifier_test = _classifier(feature_dim,no_classes)
classifier_test = torch.load('trained2_color_35000.t7')

correct = 0
for j in range(no_training_samples):
 #print obj[split+j]['color_id']
 x = train[j]
 #print obj[split+j]
 input = Variable(torch.FloatTensor(x)).view(1,-1)
 predicted = classifier_test(input)
 #out = torch.sigmoid(predicted).data > 0.2
 #print out
 maxim,idx = torch.max(torch.sigmoid(predicted).data,1)
 #print 'Prediction is:',idx[0]
 if idx[0]==obj[j]['color_id']:
 	correct += 1

print 'Training set accuracy is:',correct

j = 0
x = train[j]
print obj[j]
input = Variable(torch.FloatTensor(x)).view(1,-1)
predicted = classifier_test(input)
out = torch.sigmoid(predicted).data > 0.5
print torch.sigmoid(predicted).data
print out 
