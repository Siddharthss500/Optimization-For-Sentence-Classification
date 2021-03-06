#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Thu Jan 11 19:00:55 2018

@author: SiddharthS
"""

import re
import numpy as np
import math
import random
import matplotlib.pyplot as plt
""" If running using command shell then uncomment the below line """
#plt.switch_backend('agg')
from matplotlib.backends.backend_pdf import PdfPages
import pickle
#pip install plotly or sudo pip install (If not installed)
from plotly.offline import plot
import plotly.graph_objs as go


# Defining the global variables
dimension = 300
alpha = 0.9
epsilon = 1e-8
gamma = 0.9
eps = [epsilon for o in range(dimension)]
mini_batch = 128
names = ['Gradient Descent','Momentum','Nesterov Accelerated Gradient','Ada grad','RMS prop']
labels = ['Stochastic','Momentum','NAG','Adagrad','RMSprop']
variants = ['Batch Gradient Method','Stochastic Gradient Method','Mini-Batch Gradient Method']

def pre_process_file(filename):
    """ Pre-processes the input file and splits the file into a positive and
     a negative file """
    newfilename = filename + '.txt'
    ipfile = open(newfilename, 'r')
    ipdata = ipfile.readlines()
    tot_len = len(ipdata)
    opdata, posopdata, negopdata = ["" for i in range(3)]
    X,Y = [[] for i in range(2)]
    for i in range(tot_len):
        x = re.sub(r"[^A-Za-z0-9(),!?\'\`]", " ", ipdata[i])
        y = x.strip()
        Y.append(int(y[-1]))
        tempval = y[:-1].strip()
        X.append(tempval)
        tempdata = X[i] + '\n'
        opdata = opdata + tempdata
    ipfile.close()
    fil_name = filename + '_Full_file.txt'
    opfile = open(fil_name,'w')
    opfile.write(opdata)
    opfile.close()
    #Splitting the file into a positive and negative review file
    #Opening the new file
    ipfile = open(fil_name,'r')
    ipdata = ipfile.readlines()
    tot_len = len(ipdata)
    ipfile.close()
    for i in range(tot_len):
        if Y[i] == 1:
            posopdata = posopdata + X[i] + '\n'
        else:
            negopdata = negopdata + X[i] + '\n'
    #Writing the pos and neg files
    #For pos file
    pos_fil_name = filename + '.pos'
    opfile = open(pos_fil_name,'w')
    opfile.write(posopdata)
    opfile.close()
    #For neg file
    neg_fil_name = filename + '.neg'
    opfile = open(neg_fil_name,'w')
    opfile.write(negopdata)
    opfile.close()
    return fil_name,pos_fil_name,neg_fil_name

def file_concat(file1,file2):
    """ Concatenates two files into one """
    # Reading the contents of first file
    ipfile1 = open(file1,'r')
    file1_contents = ipfile1.read()
    ipfile1.close()
    # Reading the contents of second file
    ipfile2 = open(file2,'r')
    file2_contents = ipfile2.read()
    ipfile2.close()
    # Writing the contents of both the files into one file
    opfile = open("output_concat_file.txt",'w')
    opfile.write(file1_contents + file2_contents)
    opfile.close()
    return "output_concat_file.txt"

def clean_file(filename):
    """ Pre-processes the positive/negative file and all the words are 
    stored as a list """
    ipfile = open(filename, 'r')
    ipdata = ipfile.readlines()
    tempdata = []
    findata = []
    k = 0
    for i in range(len(ipdata)):
        x = re.sub(r"[^A-Za-z0-9(),!?\'\`]", " ", ipdata[i])
        y = x.strip()
        updatedata = y.split(' ')
        for j in updatedata:
            tempdata.append(j)
            k += 1    
    ipfile.close
    #Creating a unique list of words
    findata = list(set(tempdata))
    return findata

def ID_list(datalist):
    """ A dictionary of IDs is created for each word in the vocabulary """
    ID = []
    worddict = {}
    wordcount = len(datalist)
    # Create a list of IDs
    for i in range(0,wordcount):
        ID.append(i)
    # Create a dictionary of words - IDs
    for i in range(len(ID)):
        worddict[datalist[i]] = ID[i]
    return worddict

def load_bin_vec(fname, vocab):
    """ Loads 300x1 word vecs from Google (Mikolov) word2vec to get an initial 
    representation for words """
    word_vecs = {}
    with open(fname, "rb") as f:
        header = f.readline()
        vocab_size, layer1_size = map(int, header.split())
        binary_len = np.dtype('float32').itemsize * layer1_size
        for line in xrange(vocab_size):
            word = []
            while True:
                ch = f.read(1)
                if ch == ' ':
                    word = ''.join(word)
                    break
                if ch != '\n':
                    word.append(ch) 
            #Getting the corresponding word representation
            if word in vocab:
               word_vecs[word] = np.fromstring(f.read(binary_len), dtype='float32')  
            else:
                f.read(binary_len)
    return word_vecs

def remaining_words(fin_data_set,vocab):
    """ To get the 300x1 vector for the remaining words, i.e which are not
    present in the first list """
    count = 0
    for word in vocab:
        if word not in fin_data_set:
            count += 1
            #Using random function to assign a 300-D vector for remaining words
            fin_data_set[word] = np.random.uniform(-0.25,0.25,dimension)
    return fin_data_set

def vec_add_sentence(filename, findataset):
    """ Averages the 300-D vector representation for each word present in a sentence
    to get one 300-D vector representation for a sentence """
    ipfile = open(filename, 'r')
    ipdata = ipfile.readlines()
    prelen = len(ipdata)
    totlen = len(ipdata) * dimension
    mat = np.zeros(totlen).reshape(prelen,dimension)
    temp = np.zeros(dimension).reshape(1,dimension)
    tempnew = np.zeros(dimension).reshape(1,dimension)
    for i in range(len(ipdata)):
        x = re.sub(r"[^A-Za-z0-9(),!?\'\`]", " ", ipdata[i])
        y = x.strip()
        updatedata = y.split(' ')
        for j in updatedata:    
            temp = findataset[j]
            tempnew = np.add(tempnew,temp)
        #Normalizing the data by dividing by the number of words in each sentence
        tempnew = np.array([k/len(updatedata) for k in tempnew])
        mat[i,] = tempnew
        tempnew = np.zeros(dimension).reshape(1,dimension)
    ipfile.close
    return mat

def one_vec(IDmapdict,posnegfile):
    """ Assigns a +1/-1 vector for the positive/negative file that is passed as 
    an input """
    totlen = len(IDmapdict)
    valmat = np.ones(totlen).reshape(totlen,1)
    if posnegfile == 'P':
        return valmat
    if posnegfile == 'N':
        return np.negative(valmat)
    
def concat(mat_pos,mat_neg):
    """ Concatenates the positive and negative file into one """
    return np.concatenate((mat_pos,mat_neg), axis = 0)

def rand_samp(mat_fin,mat_score):
    """ Shuffles the data in order to create the train/valid/test datasets """
    prelen = len(mat_score)
    randtest = random.sample(range(0,prelen),prelen)
    totlen = prelen * dimension
    matnew = np.zeros(totlen).reshape(prelen,dimension)
    matscorenew = np.zeros(prelen).reshape(prelen,1)
    j = 0
    for i in randtest:
        matnew[j] = mat_fin[i]
        matscorenew[j] = mat_score[i]
        j += 1
    return matnew,matscorenew

def gen_train_valid_test(mat_fin,mat_score):
    """ Creates training/validation/test datasets in the division of 60/20/20
     in order to get the datasets ready for classification and learning """
    totlen = len(mat_score)
    train_num = int(math.floor(0.6 * totlen))
    valid_num = int(math.floor(0.2 * totlen))
    test_num = totlen - train_num - valid_num
    # Creating the training dataset
    train_num_tot = train_num * dimension
    train = np.zeros(train_num_tot).reshape(train_num,dimension)
    train_score = np.zeros(train_num)
    j = 0
    for i in range(0,train_num):
        train[j] = mat_fin[i]
        train_score[j] = mat_score[i]
        j += 1
    # Creating the validation dataset
    valid_num_tot = valid_num * dimension
    valid = np.zeros(valid_num_tot).reshape(valid_num,dimension)
    valid_score = np.zeros(valid_num)
    j = 0
    valid_updt = train_num + valid_num
    for i in range(train_num,valid_updt):
        valid[j] = mat_fin[i]
        valid_score[j] = mat_score[i]
        j += 1
    # Creating the test dataset
    test_num_tot = test_num * dimension
    test = np.zeros(test_num_tot).reshape(test_num,dimension)
    test_score = np.zeros(test_num)
    j = 0
    test_updt = valid_updt + test_num
    for i in range(valid_updt,test_updt):
        test[j] = mat_fin[i]
        test_score[j] = mat_score[i]
        j += 1
    return train,train_score,valid,valid_score,test,test_score

def log_regress(X,W,Y):
    """ Checks the accuracy of the model """
    #Calculating the actual variable output using the model parameter and 300-D vector
    inter_val = np.zeros(len(X))
    total = np.zeros(len(X))
    count = 0
    tot_len = len(X)
    for i in range(0,tot_len):
        inter_val[i] = 1/(1 + math.exp(-np.matmul(np.transpose(W),X[i])))
        #Assigning +1/-1 based on the formulae
        if inter_val[i] > 0.5:
            total[i] = 1
        else:
            total[i] = -1
    #Checking the label vector calculated versus the acutal label vector
    fin_acc = total - np.transpose(Y)
    for j in fin_acc:
        if j == 0:
            count += 1
    #Returning the accuracy rounded off after 2 decimal points
    return total,round((float(count)/float(len(Y))*100),2)

def obj_func(Y,W,X):
    """ Calculates the value of the objective function """
    fin_total = 0
    tot_len = len(X)
    for i in range(0,tot_len):
        exp_val = float(np.array([-1]) * np.array([Y[i]]) * (np.matmul(np.transpose(W),X[i])))
        fin_val = math.log(1 + math.exp(exp_val))
        fin_total += fin_val
    #Returning the normalized output of the objective function by dividing by total no. of sentences
    return (fin_total/tot_len)

def obj_func_stoc_mini(Y,W,X,index,method):
    """ Calculates the value of the objective function for gradient check """
    fin_total = 0
    tot_len = len(index)
    for i in index:
        if method == 2:
            #For Stochastic method
            exp_val = float(np.array([-1]) * np.array([Y[i]]) * (np.matmul(np.transpose(W),X)))
        else:
            #For Mini-batch method
            exp_val = float(np.array([-1]) * np.array([Y[i]]) * (np.matmul(np.transpose(W),X[i])))
        fin_val = math.log(1 + math.exp(exp_val))
        fin_total += fin_val
    #Returning the normalized output of the objective function by dividing by total no. of sentences
    return (fin_total/tot_len)

def derv_func(Y,W,X,index,method):
    """ Calculates the value of the model parameter using the derivative of 
    the objective function """
    mid = np.zeros(dimension)
    total = np.zeros(dimension)
    tot_len = len(index)
    #The derivative is calculated w.r.t the model parameters
    for i in index:    
        #Calculating the common terms
        exp_val = float(np.array([-1]) * np.array([Y[i]]) * (np.matmul(np.transpose(W),X[i])))
        #Calculating the numerator
        sub_term = float(-1 * Y[i] * math.exp(exp_val))
        num_val = [a * sub_term for a in X[i]]
        #Calculating the denominator
        den_val = 1 + math.exp(exp_val)
        mid_val = np.array([ b/den_val for b in num_val])
        total = np.array(mid) + np.array(mid_val)
        mid = total
    #Calculating the normalized output of the derivative function by dividing by total no. of sentences
    total = total/tot_len
    return total

def derv_grad_check(Y,W,X,index,method):
    """ Verifys the gradient calculated by the derivative function for 
    model parameters"""    
    # The formulae used to check is (f(x+h) - f(x-h))/2h where f(x) is the 
    # objective function and h is delta in this case
    delta_new = 1e-4
    zeros = np.zeros(dimension)
    total = np.zeros(dimension)
    for i in range(0,dimension):
        zeros[i] = 1
        new_theta =  zeros * delta_new
        if method == 1:
            theta_plus = obj_func(Y,W+new_theta,X)
            theta_minus = obj_func(Y,W-new_theta,X)
        elif method == 2:
            val = index[0]
            theta_plus = obj_func_stoc_mini(Y,W+new_theta,X[val],index,method)
            theta_minus = obj_func_stoc_mini(Y,W-new_theta,X[val],index,method)
        else:
            theta_plus = obj_func_stoc_mini(Y,W+new_theta,X,index,method)
            theta_minus = obj_func_stoc_mini(Y,W-new_theta,X,index,method)
        total[i] = (theta_plus - theta_minus)/ (2*delta_new)
        if method == 3:
            total[i] /= len(index)
        zeros = np.zeros(dimension)
    return total

def grad_desc(Y,new_W,new_X,index,method):
    """ Gradient Descent algorithm """
    #After various number of tests, the learning rates were decided as follows:
    eta = 8
    #Computing the gradient value
    derv_value = derv_func(Y,new_W,new_X,index,method)
    #print "The value calculated using derivative function is", derv_value
    #print "The value to verify the gradient output is ", derv_grad_check(Y,new_W,new_X,index,method)
    #Computing the delta change
    fin_derv_value = [k * eta for k in derv_value]
    return np.array(fin_derv_value)

def momentum(Y,new_W,new_X,index,method,new_chnge):
    """ Momentum algorithm """
    #After various number of tests, the learning rates were decided as follows:
    eta = 6
    old_chnge = new_chnge
    #Computing the gradient value
    derv_value = derv_func(Y,new_W,new_X,index,method)
    #print "The value calculated using derivative function is", derv_value
    #print "The value to verify the gradient output is ", derv_grad_check(Y,new_W,new_X,index,method)
    #Computing the delta change
    fin_derv_value = [k * eta for k in derv_value]
    #Calculating the momentum change
    momtm_chnge = [p * alpha for p in old_chnge]
    new_chnge = np.array(momtm_chnge) - np.array(fin_derv_value)
    return new_chnge

def nest_acclr_grad(Y,new_W,new_X,index,method,new_chnge):
    """ Nesterov Accelerated Gradient algorithm """
    #After various number of tests, the learning rates were decided as follows:
    eta = 6
    old_chnge = new_chnge
    new_W = np.array(new_W) + np.array([e * alpha for e in old_chnge])
    #Computing the gradient value
    derv_value = derv_func(Y,new_W,new_X,index,method)
    #print "The value calculated using derivative function is", derv_value
    #print "The value to verify the gradient output is ", derv_grad_check(Y,new_W,new_X,index,method)
    #Calculating the derivative function
    fin_derv_value = [k * eta for k in derv_value]
    #Calculating the momentum change
    momtm_chnge = [l * alpha for l in old_chnge]
    #Final computation
    new_chnge = np.array(momtm_chnge) - np.array(fin_derv_value)
    return new_chnge

def ada_grad(Y,new_W,new_X,index,method,temp_xy):
    """ Adaptive  gradient algorithm """
    #After various number of tests, the learning rates were decided as follows:
    eta = 4e-1
    old_val = temp_xy
    #Computing the gradient value
    derv_value = derv_func(Y,new_W,new_X,index,method)
    #print "The value calculated using derivative function is", derv_value
    #print "The value to verify the gradient output is ", derv_grad_check(Y,new_W,new_X,index,method)
    #Calculating the new update value of Gt
    #Squaring each value in the vector before adding it up to get Gt
    temp_xy = np.array(old_val) + np.array([t * t for t in derv_value])
    den_xy = np.array(eps) + np.array([pow(s,0.5) for s in temp_xy])
    num_xy = [-eta * k for k in derv_value]
    fin_derv_value = np.array(num_xy) / np.array(den_xy)
    return fin_derv_value,temp_xy

def rms_prop(Y,new_W,new_X,index,method,new_xy):
    """ RMS propagation algorithm """
    #After various number of tests, the learning rates were decided as follows:
    eta = 1e-2
    init_value = new_xy
    #Computing the gradient value
    derv_value = derv_func(Y,new_W,new_X,index,method)
    #print "The value calculated using derivative function is", derv_value
    #print "The value to verify the gradient output is ", derv_grad_check(Y,new_W,new_X,index,method)
    #Squaring each value in the gradient
    sqr_derv_value = [g * g for g in derv_value]
    new_xy = np.array([gamma * m for m in init_value]) + np.array([(1-gamma) * t for t in sqr_derv_value]) 
    mid_xy = np.sqrt(np.array(new_xy)) + np.array(eps)
    mid_derv_value = np.array(derv_value) / np.array(mid_xy)
    fin_derv_value = [k * eta for k in mid_derv_value]
    return fin_derv_value,new_xy

def model_parameter_optimize(algo,Y,new_W,new_X,index,method,new_chnge):
    """ Model parameter optimization for various gradient descent algorithms """
    #The corresponding algorithm is selected
    if algo == 0:
        #For gradient descent algorithm
        new_W = np.array(new_W) - grad_desc(Y,new_W,new_X,index,method)
    elif algo == 1:
        #For momemtum algorithm
        new_chnge = momentum(Y,new_W,new_X,index,method,new_chnge)
        new_W = np.array(new_W) + new_chnge
    elif algo == 2:
        #For nesterov accelerated gradient algorithm
        new_chnge = nest_acclr_grad(Y,new_W,new_X,index,method,new_chnge)
        new_W = np.array(new_W) + new_chnge
    elif algo == 3:
        #For adagrad algorithm
        delta_W,new_chnge = ada_grad(Y,new_W,new_X,index,method,new_chnge)
        new_W = np.array(new_W) + delta_W
    elif algo == 4:
        #For rmsprop algorithm
        delta_W,new_chnge = rms_prop(Y,new_W,new_X,index,method,new_chnge)
        new_W = np.array(new_W) - delta_W
    return new_W,new_chnge

def show_accuracy(i,new_X,new_W,Y,valid,valid_scre,test,test_scre):
    """ Prints the training, validation and test accuracy while optimizing 
    model parameters """
    word = 'model parameter'
    #For training accuracy
    log_reg_val,train_accuracy = log_regress(new_X,new_W,Y)
    print "After epoch" , (i+1) , "the training accuracy of " + word + " is" , train_accuracy
    #For validation accuracy
    log_reg_val,valid_accuracy = log_regress(valid,new_W,valid_scre)
    print "After epoch" , (i+1) , "the validation accuracy of " + word + " is" , valid_accuracy
    #For test accuracy
    log_reg_val,test_accuracy = log_regress(test,new_W,test_scre)
    print "After epoch" , (i+1) , "the test accuracy of " + word + " is" , test_accuracy
    return train_accuracy,valid_accuracy,test_accuracy
    

def grad_algo(train,train_scre,valid,valid_scre,test,test_scre,W,method,epoch,algo):
    """ Five Optimization algorithms are implemented in order to optimize model 
    parameters for three gradient descent variants """
    # Setting the initial values
    #Setting the internal count for no. of iterations
    inn_val = 100
    inn_count = inn_val * epoch
    iterations = range(0,inn_count)
    inn_loop_count = 0
    #Creating empty list for initial variables
    train_acc,valid_acc,test_acc,obj_func_values = (np.zeros(inn_count) for i in range(4))
    var_values = [[] for i in range(inn_count)]
    #Creating the training/validation/test datasets
    new_W = W
    new_X = train
    Y = train_scre
    tot_len = len(new_X)
    new_chnge = np.zeros(dimension)
    total_iterations = int(math.ceil(float(tot_len)/mini_batch))
    for i in range(0,epoch):
        if method == 1:
            """ For Batch method """
            index = range(0,tot_len)            
            for z in range(0,inn_val):
                #Storing the values of the objective function in a list
                obj_func_values[inn_loop_count] = obj_func(Y,new_W,new_X)
                print obj_func_values[inn_loop_count]
                #Calling the corresponding optimization algorithm to compute the new model parameter
                new_W,new_chnge = model_parameter_optimize(algo,Y,new_W,new_X,index,method,new_chnge)
                #Storing the updated value of model parameter
                var_values[inn_loop_count] = new_W
                #Computing the logistic regression and accuracy for training,validation and test dataset
                train_accuracy,valid_accuracy,test_accuracy = show_accuracy(inn_loop_count,new_X,new_W,Y,valid,valid_scre,test,test_scre)
                print "\n"
                #Storing the training/validation/test accuracies
                train_acc[inn_loop_count] = train_accuracy
                valid_acc[inn_loop_count] = valid_accuracy
                test_acc[inn_loop_count] = test_accuracy
                inn_loop_count += 1
        else:
            """ For stochastic method and mini-batch method """
            for z in range(0,inn_val):
                randtest = random.sample(range(0,len(new_X)),len(new_X))
                low = 0
                upp = mini_batch
                #For stochastic method
                if method == 2:
                    inner_iterations = randtest
                #For mini-batch method
                if method == 3:
                    inner_iterations = range(0,total_iterations)                
                #Storing the values of the objective function in a list
                obj_func_values[inn_loop_count] = obj_func(Y,new_W,new_X)
                print obj_func_values[inn_loop_count]
                for j in inner_iterations:
                    if method == 2:
                        index = [randtest[j]]
                    if method == 3:
                        index = randtest[low:upp]
                    #Calling the corresponding optimization algorithm to compute the new model parameter
                    new_W,new_chnge = model_parameter_optimize(algo,Y,new_W,new_X,index,method,new_chnge)
                    #Storing the updated value of model parameter
                    var_values[inn_loop_count] = new_W
                    #Updating the index values
                    if j!=(total_iterations - 2):
                        low += mini_batch
                        upp += mini_batch
                    else:
                        low = upp
                        upp = tot_len
                #Computing the logistic regression and accuracy for training,validation and test dataset
                train_accuracy,valid_accuracy,test_accuracy = show_accuracy(inn_loop_count,new_X,new_W,Y,valid,valid_scre,test,test_scre)
                print "\n"
                #Storing the training/validation/test accuracies
                train_acc[inn_loop_count] = train_accuracy
                valid_acc[inn_loop_count] = valid_accuracy
                test_acc[inn_loop_count] = test_accuracy
                inn_loop_count += 1
    #Obtaining the best model by finding the best validation accuracy
    best_valid_acc = max(valid_acc)
    #Finding which epoch has the best validation accuracy
    epoch_list = [f for f in iterations if valid_acc[f] == best_valid_acc]
    fin_epoch_val = min(epoch_list)
    #Getting the corresponding test accuracy
    correspdng_test_acc = test_acc[fin_epoch_val]
    #Cross-checking by finding the best test accuracy and finding the corresponding validation accuracy
    best_test_acc = max(test_acc)
    #Finding which epoch has the best test accuracy
    epoch_list_2 = [f for f in iterations if test_acc[f] == best_test_acc]
    fin_epoch_val_2 = min(epoch_list_2)
    #Getting the corresponding validation accuracy
    correspdng_valid_acc = test_acc[fin_epoch_val_2]
    print "\n"
    print "Final value of model parameter after update ", var_values[i]
    print "Output of the objective function ", obj_func_values[i]
    plt.plot(iterations,obj_func_values)
    plt.xlabel('No. of epochs')
    plt.ylabel('Objective function output')
    plt.title(names[algo])
    plt.show()
    return iterations,obj_func_values,var_values[i],train_acc,valid_acc,test_acc,best_valid_acc,fin_epoch_val,correspdng_test_acc,best_test_acc,fin_epoch_val_2,correspdng_valid_acc

def gradient_descent(mat_fin,mat_score,method,epoch,filenames):
    """ Runs all the optimization algorithms for various methods """
    #Setting the initial value
    np.random.seed(0)
    W_val = np.random.rand(dimension)
    numbers = [0,1,2,3,4]
    if method == 1:
        word = variants[0]
    elif method == 2:
        word = variants[1]
    else:
        word = variants[2]
    filname = 'Algorithms ' + word + ' ' + filenames
    filname2 = 'Algorithms ' + word + ' ' + filenames + ' Best Validation'
    filname3 = 'Algorithms ' + word + ' ' + filenames + ' Best Test'
    #Shuffling the complete data before splitting the data into training/validation/test
    mat_fin,mat_score = rand_samp(mat_fin,mat_score)
    #Splitting the data into train/valid/test datasets
    train,train_scre,valid,valid_scre,test,test_scre = gen_train_valid_test(mat_fin,mat_score)
    #Opening a file and dumping all the data
    file_name = open(filname,"wb")
    #Opening a file and dumping the accuracies for the best validation model
    file_name2 = open(filname2,"wb")
    #Opening a file and dumping the accuracies for the best test model
    file_name3 = open(filname3,"wb")
    for i in numbers:    
        print "Running ",names[i],"algorithm using",word,"\n"
        iter_1, obj_vals_1, var_vals_1,train_acc,valid_acc,test_acc,best_valid_acc,fin_epoch_val,correspdng_test_acc,best_test_acc,fin_epoch_val_2,correspdng_valid_acc = grad_algo(train,train_scre,valid,valid_scre,test,test_scre,W_val,method,epoch,i)
        #Dumping the data in the file
        pickle.dump(iter_1,file_name)
        pickle.dump(obj_vals_1,file_name)
        pickle.dump(train_acc,file_name)
        pickle.dump(valid_acc,file_name)
        pickle.dump(test_acc,file_name)
        #Dumping the best model validation,test accuracies along with its epoch number
        pickle.dump(best_valid_acc,file_name2)
        pickle.dump(fin_epoch_val,file_name2)
        pickle.dump(correspdng_test_acc,file_name2)
        #Dumping the best values for the best test accuracies for cross vaidation
        pickle.dump(best_test_acc,file_name3)
        pickle.dump(fin_epoch_val_2,file_name3)
        pickle.dump(correspdng_valid_acc,file_name3)
    file_name.close()
    file_name2.close()
    file_name3.close()
    return filname,filname2,filname3

def plot_graph(filename):
    """ Plots the graphs """
    #Setting the initial values
    n_rows = 4
    n_cols = 3
    count = 0
    X_axis = ['Objective Function','Training Accuracy','Validation Accuracy','Test Accuracy']
    iters,obj_vals,train_acc,valid_acc,test_acc = ({} for i in range(5))
    for i in range(0,15):
        if i % 5 == 0:
            files = open(filename[count],"rb")
            count += 1
        iters[i] = pickle.load(files)
        obj_vals[i] = pickle.load(files)
        train_acc[i] = pickle.load(files)
        valid_acc[i] = pickle.load(files)
        test_acc[i] = pickle.load(files)
    files.close()
    terms = [obj_vals,train_acc,valid_acc,test_acc]
    #Combining all the methods and printing the values from the file
    fig,axis = plt.subplots(4,3)
    for i in range(0,n_rows):
        temp_count = 0
        for j in range(0,n_cols):
            for k in range(0,5):
                title = 'Comparison of ' + X_axis[i] + ' vs. No. of epochs'
                axis[i,j].plot(iters[temp_count],terms[i][temp_count],label = labels[k])
                axis[i,j].set_title(title)
                axis[i,j].set_xlabel('No. of epochs')
                axis[i,j].set_ylabel(X_axis[i])
                axis[i,j].legend(loc='best')
                temp_count += 1
    fig.subplots_adjust(left=0.05, bottom=None, right=3.0, top=5.5, wspace=0.3, hspace=0.2)
    return fig

def store_table(filename,table):
    """ Creates tables of the best validation and test accuracy in order to
    identify the best model """
    count = 0
    #Setting the inital parameters
    valid_acc,epoch_no,test_acc = ([0,0,0,0,0] for i in range(3))
    valid_acc_all,epoch_no_all,test_acc_all = ({} for i in range(3))
    for i in range(0,3):
        files = open(filename[count],"rb")
        count += 1
        for j in range(0,5):
            valid_acc[j] = pickle.load(files)
            epoch_no[j] = pickle.load(files)
            test_acc[j] = pickle.load(files)
        valid_acc_all[i] = list(valid_acc)
        epoch_no_all[i] = list(epoch_no)
        test_acc_all[i] = list(test_acc)
        files.close()
    if table == 1:
        vals = ['Algorithm Name', 'Best Validation Accuracy', 'Epoch number', 'Corresponding Test Accuracy']
    else:
        vals = ['Algorithm Name', 'Best Test Accuracy', 'Epoch number', 'Corresponding Validation Accuracy']
    #Creating the table
    for i in range(0,3):
        trace = go.Table(
                header=dict(values=vals),
                cells=dict(values=[names,
                                   valid_acc_all[i],
                                   epoch_no_all[i],
                                   test_acc_all[i]]),
                name='Test')
        data = [trace]
        fil_name = filename[i] + '.html'
        plot(data,filename=fil_name)

def store_graph(fig):
    """Stores all the figures to create one PDF output """
    title = 'Optimization Results for Model Parameters'
    filname = 'Only_Model_Parameters_Optimization_Results_Final.pdf'
    with PdfPages(filname) as pdf:
        plt.figure() 
        plt.axis('off')
        plt.text(0.49,0.4,title,ha='center',va='center')
        pdf.savefig()
        pdf.savefig(fig,bbox_inches='tight')

if __name__ == "__main__":
    #The input files that we will be using for running the experiments
    filname, posfile, negfile = [['','',''] for i in range(0,3)]
    filenames = ['amazon_cells_labelled','imdb_labelled','yelp_labelled']
    datafilname = 'GoogleNews-vectors-negative300.bin'
    fig = plt.subplots(4,3)
    fil_name,fil_name2,fil_name3 = [['','',''] for r in range(3)]
    #Taking input for no. of epochs to run
    print "Please enter the no. of epochs the program has to run"
    epoch_val = long(raw_input())    
    #Loop to run over each dataset
    for i in range(0,3):
        filname[i],posfile[i],negfile[i] = pre_process_file(filenames[i])
        print "Running the program for", filenames[i], "dataset \n"
        print "The input file has been converted to the required input format \n"
        # Concatenating both the files into one file
        output_file = file_concat(posfile[i],negfile[i])
        print "Both the files are concatenated into one file \n"
        # Pre-process the data from the file
        main_file = clean_file(output_file)
        print "Pre-processing of data complete! \n"
        # Getting the IDs for the dataset for loading the 300-D vectors
        IDfull_list = ID_list(main_file)
        print "ID list is generated \n"
        # Get the corresponding 300-D vectors for all the words possible
        vecdataset = load_bin_vec(datafilname,IDfull_list)
        print "The word2vec dataset has been loaded... \n"
        # For the remaining words asign random 300-D vectors
        newvecdataset = remaining_words(vecdataset,main_file)
        print "300-D vectors are created for the words that are not present in that file \n"
        # Create the final dataset by averaging the 300-D vectors for each words in a sentence
        # For positive file
        pos_matrixdata = vec_add_sentence(posfile[i],newvecdataset)
        # For negative file
        neg_matrixdata = vec_add_sentence(negfile[i],newvecdataset)
        print "For each sentence a 300D vector is created by adding the 300D vectors of the words in the sentence \n"
        # Creating the 1-D label vectors for the positive and negative file
        pos_neg_val = 'P'
        pos_score = one_vec(pos_matrixdata,pos_neg_val)
        pos_neg_val = 'N'
        neg_score = one_vec(neg_matrixdata,pos_neg_val)
        print "Created 1-D score vectors for the positive/negative reviews with +1/-1 \n"
        # Concatenating both the files into one
        mat_fin = concat(pos_matrixdata,neg_matrixdata)
        mat_score = concat(pos_score,neg_score)
        print "Combined the two files into one single file \n"
        #Implementation of the logistic regression using objective function
        #Optimizing the model parameters by using various optimization algorithms
        print "The various algorithms for mini-batch variant are run \n"
        #Running only Mini-Batch Method
        method = 3
        fil_name[i],fil_name2[i],fil_name3[i] = gradient_descent(mat_fin,mat_score,method,epoch_val,filenames[i])
        print "\n"
        print "The code has completed running for " + filenames[i] + " dataset \n"
    print "Plotting all the graphs"
    fig = plot_graph(fil_name)
    print "Storing all the graphs in a pdf file"
    store_graph(fig)
    table = 1
    print "Creating the table1"
    store_table(fil_name2,table)
    table = 0
    print "Creating the table2"
    store_table(fil_name3,table)
    print "The code has successfully completed running!! \n"

"""
To run the code in the background:
(echo 15| nohup python Sentence_Classification_Opt_Model_Param.py > Sentence_Classification_Opt_Model_Param_log_file.txt)&

"""
