import os.path as osp
import torch
from torch_geometric.data import Dataset, Data
import itertools
import numpy as np
import uproot
import glob
import multiprocessing
from pathlib import Path
import tqdm

class GraphDataset(Dataset):
    def __init__(self, root, features, labels, spectators, transform=None, pre_transform=None,
                 n_events=-1, n_events_merge=1000):
        """
        Initialize parameters of graph dataset
        Args:
            root (str): path
            n_events (int): how many events to process (-1=all)
            n_events_merge (int): how many events to merge
        """
        self.features = features
        self.labels = labels
        self.spectators = spectators
        self.n_events = n_events
        self.n_events_merge = n_events_merge
        super(GraphDataset, self).__init__(root, transform, pre_transform)

    @property
    def raw_file_names(self):
        """
        Determines which file is being processed
        """
        files = ['root://eospublic.cern.ch//eos/opendata/cms/datascience/HiggsToBBNtupleProducerTool/HiggsToBBNTuple_HiggsToBB_QCD_RunII_13TeV_MC/train/ntuple_merged_10.root']

        return files

    @property
    def processed_file_names(self):
        """
        Returns a list of all the files in the processed files directory
        """
        proc_list = glob.glob(osp.join(self.processed_dir, 'data*.pt'))
        return_list = list(map(osp.basename, proc_list))
        return return_list

    def __len__(self):
        return len(self.processed_file_names)

    def download(self):
        # Download to `self.raw_dir`.
        pass

    def process(self):
        """
        Handles conversion of dataset file at raw_path into graph dataset.

        Args:
            raw_path (str): The absolute path to the dataset file
            k (int): Number of process (0,...,max_events // n_proc) to determine where to read file
        """
        for raw_path in self.raw_file_names:
            root_file = uproot.open(raw_path)

            tree = root_file['deepntuplizer/tree']

            feature_array = tree.arrays(branches=self.features,
                                        entrystop=self.n_events,
                                        namedecode='utf-8')

            label_array_all = tree.arrays(branches=self.labels,
                                          entrystop=self.n_events,
                                          namedecode='utf-8')
            
            n_samples = label_array_all[self.labels[0]].shape[0]

            y = np.zeros((n_samples,2))
            y[:,0] = label_array_all['sample_isQCD'] * (label_array_all['label_QCD_b'] + \
                                                        label_array_all['label_QCD_bb'] + \
                                                        label_array_all['label_QCD_c'] + \
                                                        label_array_all['label_QCD_cc'] + \
                                                        label_array_all['label_QCD_others'])
            y[:,1] = label_array_all['label_H_bb']


            spec_array = tree.arrays(branches=self.spectators,
                                     entrystop=self.n_events,
                                     namedecode='utf-8')
            z = np.stack([spec_array[spec] for spec in self.spectators],axis=1)


            for i in tqdm.tqdm(range(n_samples)):
                if i%self.n_events_merge == 0:
                    datas = []
                n_particles = len(feature_array[self.features[0]][i])
                if n_particles<1: continue
                pairs = np.stack([[m, n] for (m, n) in itertools.product(range(n_particles),range(n_particles)) if m!=n])
                edge_index = torch.tensor(pairs, dtype=torch.long)
                edge_index=edge_index.t().contiguous()
                x = torch.tensor([feature_array[feat][i] for feat in self.features], dtype=torch.float).T
                u = torch.tensor(z[i], dtype=torch.float)
                data = Data(x=x, edge_index=edge_index, y=torch.tensor(y[i:i+1],dtype=torch.int))
                data.u = torch.unsqueeze(u, 0)
                if self.pre_filter is not None and not self.pre_filter(data):
                    continue
                if self.pre_transform is not None:
                    data = self.pre_transform(data)
                datas.append([data])

                if i%self.n_events_merge == self.n_events_merge-1:
                    datas = sum(datas,[])
                    torch.save(datas, osp.join(self.processed_dir, 'data_{}.pt'.format(i)))

    def get(self, idx):
        p = osp.join(self.processed_dir, self.processed_file_names[idx])
        data = torch.load(p)
        return data

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=str, help="dataset path", required=True)
    parser.add_argument("--n-events", type=int, default=-1, help="number of events (-1 means all)")
    parser.add_argument("--n-events-merge", type=int, default=1000, help="number of events to merge")
    args = parser.parse_args()

    # 48 track-level features
    features = ['track_pt',
            'track_ptrel',
            'trackBTag_Eta',
            'trackBTag_DeltaR',
            'trackBTag_EtaRel',
            'trackBTag_JetDistVal',
            'trackBTag_Momentum',
            'trackBTag_PPar',
            'trackBTag_PParRatio',
            'trackBTag_PtRatio',
            'trackBTag_PtRel',
            'trackBTag_Sip2dSig',
            'trackBTag_Sip2dVal',
            'trackBTag_Sip3dSig',
            'trackBTag_Sip3dVal',
            'track_VTX_ass',
            'track_charge',
            'track_deltaR',
            'track_detadeta',
            'track_dlambdadz',
            'track_dlambdadz',
            'track_dphidphi',
            'track_dphidxy',
            'track_dptdpt',
            'track_drminsv',
            'track_drsubjet1',
            'track_drsubjet2',
            'track_dxy',
            'track_dxydxy',
            'track_dxydz',
            'track_dxysig',
            'track_dz',
            'track_dzdz',        
            'track_dzsig',
            'track_erel',
            'track_etarel',
            'track_fromPV',
            'track_isChargedHad',
            'track_isEl',
            'track_isMu',
            'track_lostInnerHits',
            'track_mass',
            'track_normchi2',            
            'track_phirel',
            'track_pt',
            'track_ptrel',
            'track_puppiw',
            'track_quality']

    # spectators to define mass/pT window
    spectators = ['fj_sdmass',
                  'fj_pt']

    # 2 labels: QCD or Hbb (we'll reduce the following labels)
    labels =  ['label_QCD_b',
               'label_QCD_bb',
               'label_QCD_c',
               'label_QCD_cc',
               'label_QCD_others',
               'sample_isQCD',
               'label_H_bb']

    gdata = GraphDataset(args.dataset, features, labels, spectators,
                         n_events=args.n_events,
                         n_events_merge=args.n_events_merge)